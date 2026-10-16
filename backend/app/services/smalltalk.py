"""闲聊与引导对话（问题三：非事项问题不再机械回复「暂不支持」）。

意图规则未命中事项时，先经本模块分流：

- **问候 / 寒暄 / 感谢 / 告别**：规则直答（不调模型，零延迟零成本）；
- **接着上文事项的追问**（如「那费用呢」）：标记 followup，由编排层沿用
  该事项走检索与生成，给出真正的回答（验收 B2）；
- **与事务沾边但表述不清**：模型生成一句引导语（smalltalk）；
- **明确库外**（食堂、选课等）：unsupported，不编造。

硬约束（修复方案 3.4 / 契约 §4.7 ③）：smalltalk 文案**不得输出政策、时间、
地点、电话与办理流程**，只做寒暄与引导。分类输出解析失败一律按
unsupported 处理，绝不臆测。
"""

import json
import re
from dataclasses import dataclass
from typing import Literal

from app.services.intent import SERVICE_NAMES
from app.services.llm_client import LLMClient

# 分类输出解析失败时的兜底引导语
GUIDE_FALLBACK = "我在呢。想办什么校园事务，和我说一声就行。"

SMALLTALK_SYSTEM_PROMPT = """你是校园办事小秘书的对话分流器，负责把「不属于支持事项关键词规则」的学生消息分成三类。

支持事项：学生证补办、校园卡补办、宿舍报修、请假办理、奖学金申请、助学金申请、转专业咨询、毕业手续。

分类口径：
1. smalltalk：寒暄、感谢、告别等与校园事务无关的对话；或与事务沾边但表述不清、需要引导的话。此时输出一句自然的回复文案（text），可以提示你能帮的方向，但不得包含任何政策内容。
2. followup：上文正在讨论的事项明确，且当前消息是在追问该事项的相关信息（例如上文在聊学生证补办，用户问「那费用呢」「需要带什么」「多久能办好」）。
3. unsupported：明确询问上述八项事务之外的校园事务（如食堂、选课、上网、图书馆借阅等）。

硬约束（违反即视为分类失败）：
- smalltalk 的 text 不得包含办理流程、所需材料、办理地点、办理时间、联系电话、截止日期、费用金额等政策内容；
- 不得替用户猜测事项；拿不准是 smalltalk 还是 unsupported 时，优先 smalltalk 引导；
- followup 只在「上文事项明确」且「本句是该事项的追问」同时成立时输出。

只输出一个 JSON 对象，不要输出解释文字或 Markdown 代码块：
{"status": "smalltalk"|"followup"|"unsupported", "text": "smalltalk 时的回复文案；其余分类填空字符串"}"""


@dataclass(frozen=True)
class SmalltalkResult:
    """分类结果：smalltalk 带文案；followup / unsupported 不带。"""

    kind: Literal["smalltalk", "followup", "unsupported"]
    text: str | None


# 问候规则表：整句（含语气词与标点）命中即直答，不调模型。
# 只做寒暄与引导，文案不得含政策内容（由 test_smalltalk 把关）。
_GREETING_REPLIES: dict[str, str] = {
    "你好": "你好，我是校园办事小秘书。学生证、校园卡、宿舍报修、请假、奖助学金这些校园事务都可以问我。",
    "您好": "您好，我是校园办事小秘书。学生证、校园卡、宿舍报修、请假、奖助学金这些校园事务都可以问我。",
    "你好呀": "你好呀，我是校园办事小秘书。学生证、校园卡、宿舍报修、请假、奖助学金这些校园事务都可以问我。",
    "您好呀": "您好呀，我是校园办事小秘书。学生证、校园卡、宿舍报修、请假、奖助学金这些校园事务都可以问我。",
    "在吗": "在的，有什么校园事务想了解，直接问我就行。",
    "在么": "在的，有什么校园事务想了解，直接问我就行。",
    "在不在": "在的，有什么校园事务想了解，直接问我就行。",
    "嗨": "嗨，我是校园办事小秘书，校园事务都可以问我。",
    "哈喽": "哈喽，我是校园办事小秘书，校园事务都可以问我。",
    "hello": "hello，我是校园办事小秘书，校园事务都可以问我。",
    "hi": "hi，我是校园办事小秘书，校园事务都可以问我。",
    "谢谢": "不客气，能帮上忙就好。还有别的事也可以问我。",
    "多谢": "不客气，能帮上忙就好。还有别的事也可以问我。",
    "感谢": "不客气，能帮上忙就好。还有别的事也可以问我。",
    "谢谢你": "不客气，能帮上忙就好。还有别的事也可以问我。",
    "谢谢啦": "不客气，能帮上忙就好。还有别的事也可以问我。",
    "再见": "再见，有事随时来找我。",
    "拜拜": "再见，有事随时来找我。",
    "早上好": "早上好，今天要办什么事，可以先和我说说。",
    "上午好": "上午好，有什么校园事务想了解吗？",
    "中午好": "中午好，记得先吃饭。校园的事也可以问我。",
    "下午好": "下午好，有什么校园事务想了解吗？",
    "晚上好": "晚上好，这么晚还在忙校园的事，要注意休息。",
    "晚安": "晚安，好梦。校园的事明天也可以问我。",
}

# 长词在前，保证「你好呀」不会被「你好」抢先匹配
_GREETING_PATTERN = re.compile(
    r"^\s*(?P<word>"
    + "|".join(sorted(_GREETING_REPLIES, key=len, reverse=True))
    + r")[\s~～!！?？。，,.、呀啊呢吧哦嘛啦]*$",
    re.IGNORECASE,
)

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def greeting_reply(message: str) -> str | None:
    """整句命中问候规则 → 直答文案（不调模型）；未命中返回 None。"""
    match = _GREETING_PATTERN.match(message or "")
    if match is None:
        return None
    return _GREETING_REPLIES.get(match.group("word").lower())


def classify(
    message: str,
    history: str | None,
    last_intent: str | None,
    llm: LLMClient,
) -> SmalltalkResult:
    """先规则后模型：命中问候规则直接返回（零成本）；否则调模型三分类。"""
    rule_text = greeting_reply(message)
    if rule_text is not None:
        return SmalltalkResult("smalltalk", rule_text)
    raw = llm.complete(
        SMALLTALK_SYSTEM_PROMPT,
        _build_classify_prompt(message, history, last_intent),
    )
    return _parse_classification(raw)


def _build_classify_prompt(
    message: str, history: str | None, last_intent: str | None
) -> str:
    name = SERVICE_NAMES.get(last_intent or "")
    item = f"{name}（{last_intent}）" if name else "无"
    return "\n".join(
        [
            f"【上文正在讨论的事项】{item}",
            "【对话历史】",
            history or "（无，这是本轮对话的第一条消息）",
            "【当前消息】",
            message,
        ]
    )


def _parse_classification(raw: str) -> SmalltalkResult:
    """解析模型输出；任何异常（无 JSON / 字段缺失 / 取值非法）都按 unsupported 兜底。"""
    text = (raw or "").strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return SmalltalkResult("unsupported", None)
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return SmalltalkResult("unsupported", None)
    if not isinstance(payload, dict):
        return SmalltalkResult("unsupported", None)
    status = str(payload.get("status", "")).strip()
    reply = payload.get("text")
    reply = reply.strip() if isinstance(reply, str) and reply.strip() else None
    if status == "smalltalk":
        return SmalltalkResult("smalltalk", reply or GUIDE_FALLBACK)
    if status == "followup":
        return SmalltalkResult("followup", None)
    return SmalltalkResult("unsupported", None)
