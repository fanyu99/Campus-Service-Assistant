"""问答主链路编排（契约 §4.3）。

六段流水线（实施方案 5.4）目前全部由后端承担：
    输入清洗 → 意图识别 → 知识检索 → 依据判断 → 大模型生成 → 输出校验
AgentArts 工作流就绪后，可将中段替换为工作流节点，本模块的入参出参不变。

关键约定：
- 只有 answered 状态返回结构化 answer，其余状态 answer 显式返回 null；
- sources 由后端从数据库映射（不采信模型输出），恒为数组；
- 会话在同一事务内落库，失败不产生半截会话。
"""

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BusinessError
from app.models import AnswerStatus, Conversation, ServiceItem
from app.schemas.chat import (
    MAX_MESSAGE_LENGTH,
    AnswerCard,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSource,
)
from app.services.intent import CLARIFY_RULES, SERVICE_NAMES, recognize_intent
from app.services.llm_client import LLMClient
from app.services.retrieval import RetrievalOutcome, retrieve_documents
from app.services.session_token import normalize_session_token

UNVERIFIED_WARNING = "该事项另有未核验或已过期的资料，具体以最新通知为准"

SYSTEM_PROMPT = """你是校园办事小秘书，只能依据给定的「知识片段」回答学生问题。

必须遵守：
1. 不得根据常识编造学校政策、时间、地点、材料和联系方式；
2. 知识片段不足以支撑完整回答时，只输出 {"status": "insufficient_evidence"}；
3. 用户信息不足时不要猜测，直接按依据不足处理；
4. 正式答案必须能对应到给定的知识片段；
5. 知识片段标注过期或冲突时不得输出确定结论；
6. 不索取身份证号、银行卡号、账号密码等敏感信息；
7. 使用简洁、可执行的步骤回答；
8. 只输出一个 JSON 对象，不要输出解释文字或 Markdown 代码块；
9. 只要知识片段包含该事项的办理条件、材料或步骤，就必须给出结构化回答，不得改判为依据不足；
10. 保持简洁：summary 不超过 50 字；eligibility / materials / steps 各不超过 5 条，
    steps 超过 5 条时必须合并同类步骤；每条不超过 40 字，contacts 不超过 2 条。

输出 JSON 结构：
{"title": "事项名称", "summary": "一句话概述", "eligibility": ["办理条件"],
 "materials": ["所需材料"], "steps": ["办理步骤"], "location": "办理地点或 null",
 "deadline": "YYYY-MM-DD 或 null", "contacts": ["联系方式"], "warnings": ["风险提示"]}
"""

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)
ParseKind = Literal["card", "insufficient", "invalid"]


@dataclass(frozen=True)
class _Outcome:
    status: AnswerStatus
    intent: str | None
    answer: AnswerCard | None
    sources: tuple[ChatSource, ...]
    clarifying_question: str | None


@dataclass(frozen=True)
class _History:
    intent: str | None
    status: AnswerStatus | None
    hint: str | None


def handle_chat_message(
    session: Session,
    payload: ChatMessageRequest,
    session_token: str | None,
    llm: LLMClient,
) -> ChatMessageResponse:
    _reject_overlong(payload.message)
    conversation = _resolve_conversation(session, payload, session_token)
    history = _history(conversation, payload)
    outcome = _run_pipeline(session, payload, llm, history)
    _persist(session, conversation, payload, outcome)
    return _to_response(conversation.id, outcome)


def _reject_overlong(message: str) -> None:
    if len(message) > MAX_MESSAGE_LENGTH:
        raise BusinessError(
            400,
            "MESSAGE_TOO_LONG",
            f"message 不能超过 {MAX_MESSAGE_LENGTH} 个字符",
        )


def _normalize_token(session_token: str | None) -> str | None:
    return normalize_session_token(session_token)


def _resolve_conversation(
    session: Session, payload: ChatMessageRequest, session_token: str | None
) -> Conversation:
    token = _normalize_token(session_token)
    if payload.conversation_id is None:
        now = datetime.now(timezone.utc)
        return Conversation(
            id=str(uuid.uuid4()),
            question=payload.message,
            # 占位值，提交前会被实际状态覆盖（列非空，避免漏设导致写入失败）
            result_status=AnswerStatus.SERVICE_ERROR,
            started_at=now,
            last_message_at=now,
            session_token=token,
        )
    conversation = session.get(Conversation, payload.conversation_id)
    if conversation is None:
        raise BusinessError(404, "CONVERSATION_NOT_FOUND", "会话不存在或已过期")
    if conversation.session_token is None:
        # 会话创建时未带标识：本次带标识访问即认领，之后按标识隔离
        conversation.session_token = token
    elif conversation.session_token != token:
        # 禁止跨标识续写（契约 §4.4 的匿名隔离要求）
        raise BusinessError(404, "CONVERSATION_NOT_FOUND", "会话不存在或已过期")
    return conversation


def _history(conversation: Conversation, payload: ChatMessageRequest) -> _History:
    """多轮上下文：会话表无消息明细，这里带上轮摘要作为模型提示。"""
    if payload.conversation_id is None:
        return _History(None, None, None)
    parts = [f"上一轮问题：{conversation.question}"]
    if conversation.last_intent:
        name = SERVICE_NAMES.get(conversation.last_intent, conversation.last_intent)
        parts.append(f"上一轮事项：{name}")
    parts.append(f"上一轮状态：{conversation.result_status.value}")
    return _History(
        intent=conversation.last_intent,
        status=conversation.result_status,
        hint="｜".join(parts),
    )


def _inherited_intent(history: _History) -> str | None:
    """上一轮是「主动追问」时，本轮视为对该追问的回答，沿用上一轮事项。

    否则用户回答「病假，三天」这类不含事项关键词的补充信息时会被误判为「暂不支持」。
    """
    if history.status is not AnswerStatus.NEED_CLARIFICATION:
        return None
    return history.intent


def _run_pipeline(
    session: Session,
    payload: ChatMessageRequest,
    llm: LLMClient,
    history: _History,
) -> _Outcome:
    intent_result = recognize_intent(payload.message)
    if intent_result.kind == "unsupported":
        inherited = _inherited_intent(history)
        if inherited is None:
            return _Outcome(AnswerStatus.UNSUPPORTED, None, None, (), None)
        rule = CLARIFY_RULES.get(inherited)
        if rule is not None and not any(keyword in payload.message for keyword in rule[0]):
            # 仍未给出关键参数 → 继续追问同一事项
            return _Outcome(
                AnswerStatus.NEED_CLARIFICATION, inherited, None, (), rule[1]
            )
        intent_code = inherited
    elif intent_result.kind == "clarify":
        return _Outcome(
            AnswerStatus.NEED_CLARIFICATION,
            intent_result.intent,
            None,
            (),
            intent_result.clarifying_question,
        )
    else:
        intent_code = intent_result.intent

    if intent_code is None:  # pragma: no cover - recognize_intent 已保证非空
        return _Outcome(AnswerStatus.UNSUPPORTED, None, None, (), None)

    retrieval = retrieve_documents(session, intent_code, payload.context)
    if retrieval.status is AnswerStatus.CONFLICT:
        return _Outcome(AnswerStatus.CONFLICT, intent_code, None, retrieval.sources, None)
    if retrieval.status is AnswerStatus.INSUFFICIENT_EVIDENCE:
        # 拒答但仍回带「存在但不可用」的来源，供前端提示资料已失效/未核验
        return _Outcome(
            AnswerStatus.INSUFFICIENT_EVIDENCE, intent_code, None, retrieval.sources, None
        )

    raw = llm.complete(
        SYSTEM_PROMPT, _build_user_prompt(payload, intent_code, retrieval, history.hint)
    )
    kind, card = _parse_answer(raw)
    if kind == "insufficient":
        return _Outcome(AnswerStatus.INSUFFICIENT_EVIDENCE, intent_code, None, (), None)
    if kind == "invalid" or card is None:
        return _Outcome(AnswerStatus.SERVICE_ERROR, intent_code, None, (), None)
    card.warnings = _merge_warnings(card.warnings, retrieval)
    return _Outcome(AnswerStatus.ANSWERED, intent_code, card, retrieval.sources, None)


def _build_user_prompt(
    payload: ChatMessageRequest,
    intent_code: str,
    retrieval: RetrievalOutcome,
    history: str | None,
) -> str:
    lines = [f"【事项】{SERVICE_NAMES.get(intent_code, intent_code)}"]
    context = payload.context
    if context is not None:
        if context.campus:
            lines.append(f"【校区】{context.campus}")
        if context.student_type:
            lines.append(f"【学生类型】{context.student_type}")
    lines.append("【知识片段】")
    for index, document in enumerate(retrieval.documents, start=1):
        lines.append(
            f"{index}. 标题：{document.title}｜发布部门：{document.department}"
            f"｜发布日期：{document.publish_date.isoformat()}"
            f"｜有效期：{document.effective_from.isoformat()}~{document.effective_to.isoformat()}"
            f"｜适用对象：{document.audience}｜适用校区：{document.campus}"
            f"｜状态：{document.status.value}"
        )
        lines.append(f"   正文：{(document.content or '').strip()}")
    if history:
        lines.append(f"【上一轮对话】{history}")
    lines.append(f"【学生问题】{payload.message}")
    return "\n".join(lines)


def _extract_json_object(text: str) -> str | None:
    """取第一个「配平」的 JSON 对象。

    模型在对象前后夹带解释文字、或多个花括号片段时，「首个 { 到末个 }」会截出非法片段，
    这里按花括号深度 + 字符串状态扫描，只取最外层完整对象。
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _parse_answer(raw: str) -> tuple[ParseKind, AnswerCard | None]:
    text = (raw or "").strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    candidate = _extract_json_object(text)
    if candidate is None:
        return "invalid", None
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return "invalid", None
    if not isinstance(payload, dict):
        return "invalid", None
    if str(payload.get("status", "")).strip() == "insufficient_evidence":
        return "insufficient", None
    try:
        return "card", AnswerCard.model_validate(payload)
    except ValidationError:
        return "invalid", None


def _merge_warnings(warnings: list[str], retrieval: RetrievalOutcome) -> list[str]:
    merged = list(warnings)
    if retrieval.has_unverified and UNVERIFIED_WARNING not in merged:
        merged.append(UNVERIFIED_WARNING)
    return merged


def _existing_intent_code(session: Session, intent_code: str | None) -> str | None:
    """会话表的 last_intent 有外键约束，事项不存在时降级为 null，避免 500。"""
    if intent_code is None:
        return None
    exists = session.scalar(select(ServiceItem.id).where(ServiceItem.code == intent_code))
    return intent_code if exists is not None else None


def _persist(
    session: Session,
    conversation: Conversation,
    payload: ChatMessageRequest,
    outcome: _Outcome,
) -> None:
    conversation.question = payload.message
    conversation.last_intent = _existing_intent_code(session, outcome.intent)
    conversation.result_status = outcome.status
    conversation.last_message_at = datetime.now(timezone.utc)
    session.add(conversation)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise


def _to_response(conversation_id: str, outcome: _Outcome) -> ChatMessageResponse:
    return ChatMessageResponse(
        conversation_id=conversation_id,
        status=outcome.status,
        intent=outcome.intent,
        answer=outcome.answer,
        sources=list(outcome.sources),
        need_clarification=outcome.status is AnswerStatus.NEED_CLARIFICATION,
        clarifying_question=outcome.clarifying_question,
    )
