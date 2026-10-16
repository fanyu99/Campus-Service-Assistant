"""意图识别（规则优先）。

AgentArts 工作流尚未搭建，实施方案第五章「意图识别」节点暂由后端规则承担：
- 用事项关键词表打分，命中唯一最高分即认定意图；
- 多个事项同分（跨事项问题）或缺少关键参数时转「主动追问」；
- 全部未命中转「暂不支持」。

关键词表可随事项扩充；后续接入工作流后，本模块可作为降级路径保留。
"""

from dataclasses import dataclass
from typing import Literal

SERVICE_NAMES: dict[str, str] = {
    "S01": "学生证补办",
    "S02": "校园卡补办",
    "S03": "宿舍报修",
    "S04": "请假办理",
    "S05": "奖学金申请",
    "S06": "助学金申请",
    "S07": "转专业咨询",
    "S08": "毕业手续",
}

INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "S01": ("学生证",),
    "S02": ("校园卡", "一卡通"),
    "S03": ("报修", "维修", "宿舍坏", "水龙头", "水管", "灯坏", "空调坏"),
    "S04": ("请假", "销假", "事假", "病假", "公假"),
    "S05": ("奖学金",),
    "S06": ("助学金", "困难补助", "助学贷款"),
    "S07": ("转专业",),
    "S08": ("毕业", "离校", "学位证", "毕业证"),
}

# 需要追问关键参数的事项（实施方案 8.4）：命中任一关键词即视为参数齐备
CLARIFY_RULES: dict[str, tuple[tuple[str, ...], str]] = {
    "S04": (
        ("事假", "病假", "公假", "假条", "请假条", "几天", "小时", "天"),
        "你的请假类型是事假、病假还是公假？",
    ),
    "S05": (
        ("国家奖学金", "校级奖学金", "院级奖学金", "励志", "一等", "二等", "三等"),
        "你想申请哪一类奖学金？",
    ),
}


@dataclass(frozen=True)
class IntentResult:
    kind: Literal["matched", "clarify", "unsupported"]
    intent: str | None
    clarifying_question: str | None


def recognize_intent(message: str) -> IntentResult:
    scores = {
        code: sum(1 for keyword in keywords if keyword in message)
        for code, keywords in INTENT_KEYWORDS.items()
    }
    best = max(scores.values(), default=0)
    if best == 0:
        return IntentResult("unsupported", None, None)

    winners = sorted(code for code, score in scores.items() if score == best)
    if len(winners) > 1:
        names = "、".join(SERVICE_NAMES[code] for code in winners)
        return IntentResult("clarify", None, f"你想办理的是{names}中的哪一项？")

    code = winners[0]
    rule = CLARIFY_RULES.get(code)
    if rule is not None:
        keywords, question = rule
        if not any(keyword in message for keyword in keywords):
            return IntentResult("clarify", code, question)
    return IntentResult("matched", code, None)
