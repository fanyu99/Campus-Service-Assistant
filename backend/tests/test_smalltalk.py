"""smalltalk 分流（问题三）的测试。

覆盖修复方案 3.6：问候规则直答（不发模型请求）、模糊问题走模型引导、
明确库外仍 unsupported、smalltalk 不含政策关键词；另覆盖 followup
（接着上文事项追问，沿用同一事项给出回答，验收 B2）与解析失败兜底。
"""

import pytest
from sqlalchemy import func, select

from app.models import Conversation, ConversationMessage
from app.services.llm_client import MockLLMClient
from app.services.smalltalk import (
    SMALLTALK_SYSTEM_PROMPT,
    classify,
    greeting_reply,
)

from tests.test_chat_api import (
    VALID_CARD,
    _document,
    _item,
    _post,
    _use_llm,
)

# smalltalk 文案不得出现的政策关键词（修复方案 3.4 红线）
POLICY_KEYWORDS = ["办理", "流程", "材料", "地点", "电话", "费用", "截止", "政策"]

GREETINGS = ["你好", "您好", "在吗", "谢谢", "再见", "早上好", "下午好", "晚安"]


class _PromptAwareLLM:
    """按 system 提示词分流的测试替身：smalltalk 分类 vs 办事卡片生成。

    MockLLMClient 只按 user 关键词匹配，而「分类」与「生成」两次调用的
    user 提示词都包含同一条学生消息（如「那费用呢」），无法区分，
    因此这里按 system 内容路由。
    """

    def __init__(self, classify_responses: dict[str, str] | None = None) -> None:
        self._classify_responses = classify_responses or {}
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if "对话分流器" in system:
            for keyword, response in self._classify_responses.items():
                if keyword in user:
                    return response
            return '{"status": "unsupported"}'
        return VALID_CARD


# ── 单元：问候规则直答 ──────────────────────────────────────────────


@pytest.mark.parametrize("message", GREETINGS + ["你好呀", "在吗？", "谢谢你", "hello", "嗨"])
def test_greeting_rule_answers_without_model(message):
    llm = MockLLMClient()
    result = classify(message, None, None, llm)
    assert result.kind == "smalltalk"
    assert result.text
    assert llm.calls == []  # 规则命中不调模型（C1：响应 <1s、零成本）


def test_greeting_with_extra_words_falls_through_to_model():
    """「谢谢你的帮助」不是纯问候：交给模型判断，不能规则直答。"""
    assert greeting_reply("谢谢你的帮助") is None


@pytest.mark.parametrize("message", GREETINGS)
def test_greeting_replies_contain_no_policy_keywords(message):
    result = classify(message, None, None, MockLLMClient())
    for keyword in POLICY_KEYWORDS:
        assert keyword not in (result.text or "")


def test_smalltalk_system_prompt_forbids_policy_content():
    assert "不得包含办理流程" in SMALLTALK_SYSTEM_PROMPT
    assert "费用金额" in SMALLTALK_SYSTEM_PROMPT


# ── 单元：模型分类与兜底 ────────────────────────────────────────────


def test_vague_question_goes_through_model_for_guidance():
    llm = _PromptAwareLLM({"办点事": '{"status": "smalltalk", "text": "你想办哪方面的事？"}'})
    result = classify("我想办点事", None, None, llm)
    assert result.kind == "smalltalk"
    assert result.text == "你想办哪方面的事？"
    assert len(llm.calls) == 1


def test_clearly_out_of_scope_stays_unsupported():
    llm = _PromptAwareLLM({"食堂": '{"status": "unsupported"}'})
    result = classify("食堂几点开门？", None, None, llm)
    assert result.kind == "unsupported"
    assert result.text is None


def test_unparseable_classification_falls_back_to_unsupported():
    llm = MockLLMClient(default="抱歉，我不太确定该怎么回答。")
    result = classify("随便说点什么", None, None, llm)
    assert result.kind == "unsupported"


def test_smalltalk_without_text_gets_fallback_reply():
    llm = _PromptAwareLLM({"你好吗": '{"status": "smalltalk"}'})
    result = classify("你好吗", None, None, llm)
    assert result.kind == "smalltalk"
    assert result.text


# ── 接口：问候 / 引导 / 库外 ────────────────────────────────────────


def test_greeting_returns_smalltalk_without_model_call(db_client):
    llm = MockLLMClient()
    _use_llm(db_client, llm)
    resp = _post(db_client, "你好？")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "smalltalk"
    assert body["intent"] is None
    assert body["answer"] is None
    assert body["sources"] == []
    assert body["need_clarification"] is False
    assert body["text"]  # 纯文本对话内容
    assert llm.calls == []


def test_vague_question_returns_smalltalk_guide(db_client):
    _use_llm(
        db_client,
        _PromptAwareLLM(
            {"办点事": '{"status": "smalltalk", "text": "你想办哪方面的事？学生证、校园卡这些我都可以帮你查。"}'}
        ),
    )
    body = _post(db_client, "我想办点事").json()
    assert body["status"] == "smalltalk"
    assert body["text"] == "你想办哪方面的事？学生证、校园卡这些我都可以帮你查。"
    assert body["answer"] is None
    assert body["sources"] == []


def test_out_of_scope_question_still_unsupported(db_client):
    _use_llm(db_client, _PromptAwareLLM({"食堂": '{"status": "unsupported"}'}))
    body = _post(db_client, "食堂几点开门？").json()
    assert body["status"] == "unsupported"
    assert body["answer"] is None
    assert body["sources"] == []
    assert body["text"] is None


def test_smalltalk_round_persists_messages(db_client, db_session):
    """smalltalk 轮同样落两条消息（问题二 + 问题三叠加）。"""
    _use_llm(db_client, MockLLMClient())
    body = _post(db_client, "谢谢你").json()
    assert body["status"] == "smalltalk"
    messages = db_session.scalars(
        select(ConversationMessage).order_by(ConversationMessage.created_at)
    ).all()
    assert len(messages) == 2
    assert messages[0].role == "question"
    assert messages[0].content == "谢谢你"
    assert messages[1].role == "assistant"
    assert messages[1].status == "smalltalk"
    assert messages[1].content == body["text"]
    assert messages[1].answer_json is None
    assert messages[1].sources_json is None


def test_followup_continues_established_item_and_answers(db_client, db_session):
    """验收 B2：续接会话里追问「那费用呢？」→ 命中同一事项并给出回答。"""
    item = _item(db_session)
    _document(db_session, item, content="办理条件：学生证遗失。\n补办费用：免费。\n所需材料：有效身份证明。")
    llm = _PromptAwareLLM({"费用": '{"status": "followup"}'})
    _use_llm(db_client, llm)

    first = _post(db_client, "学生证丢了怎么补办？").json()
    assert first["status"] == "answered"
    second = _post(db_client, "那费用呢？", conversation_id=first["conversation_id"]).json()

    assert second["conversation_id"] == first["conversation_id"]
    assert second["status"] == "answered"
    assert second["intent"] == "S01"
    assert second["answer"]["title"] == "学生证补办"
    # 追问轮带上了对话历史，模型据此生成
    assert "【对话历史】" in llm.calls[-1][1]
    assert "学生：学生证丢了怎么补办？" in llm.calls[-1][1]
    # 全程同一个会话，未新开
    assert db_session.scalar(select(func.count()).select_from(Conversation)) == 1


def test_followup_without_established_item_stays_unsupported(db_client):
    """模型误判 followup 但上文无明确事项时，按 unsupported 兜底。"""
    _use_llm(db_client, _PromptAwareLLM({"那个": '{"status": "followup"}'}))
    body = _post(db_client, "那个怎么办").json()
    assert body["status"] == "unsupported"


def test_out_of_scope_followup_after_answer_is_not_inherited(db_client, db_session):
    """上一轮 answered 后问库外问题：分类器判 unsupported，不沿用事项。"""
    item = _item(db_session)
    _document(db_session, item)
    _use_llm(db_client, _PromptAwareLLM({"食堂": '{"status": "unsupported"}'}))
    first = _post(db_client, "学生证丢了怎么补办？").json()
    second = _post(
        db_client, "食堂几点开门？", conversation_id=first["conversation_id"]
    ).json()
    assert second["status"] == "unsupported"
    assert second["intent"] is None


def test_smalltalk_after_answer_does_not_break_next_real_question(db_client, db_session):
    """answered → 寒暄 → 再问事项：寒暄不污染后续意图识别。"""
    item = _item(db_session)
    _document(db_session, item)
    other = _item(db_session, code="S02", name="校园卡补办")
    _document(db_session, other, title="关于校园卡补办的通知")
    llm = _PromptAwareLLM({"谢谢": '{"status": "smalltalk", "text": "不客气。"}'})
    _use_llm(db_client, llm)

    first = _post(db_client, "学生证丢了怎么补办？").json()
    assert first["status"] == "answered"
    thanks = _post(db_client, "谢谢你", conversation_id=first["conversation_id"]).json()
    assert thanks["status"] == "smalltalk"
    third = _post(db_client, "校园卡丢了怎么办？", conversation_id=first["conversation_id"]).json()
    assert third["status"] == "answered"
    assert third["intent"] == "S02"


def test_clarify_chain_still_takes_priority_over_smalltalk(db_client, db_session):
    """「追问补参」链优先于 smalltalk 分流：病假参数答复仍走原逻辑。"""
    item = _item(db_session, code="S04", name="请假办理")
    _document(db_session, item, title="关于请假办理的通知")
    _use_llm(db_client, _PromptAwareLLM())
    first = _post(db_client, "我想请假。").json()
    assert first["status"] == "need_clarification"
    second = _post(db_client, "病假，三天", conversation_id=first["conversation_id"]).json()
    assert second["status"] == "answered"
    assert second["intent"] == "S04"
