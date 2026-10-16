"""输入清洗与输出白名单（契约 §6.6 / §6.7、OWASP A03 / A08）。

原则：
- ``message`` 会直达大模型 / 智能体工作流，不能只靠提示词软约束，后端必须先做硬校验；
- 命中敏感数据或提示词注入时**直接拒绝**（不脱敏、不入库、不进日志）——脱敏会把敏感值
  留在请求链路里，拒绝更彻底；
- 只对「敏感数据的取值」判罚，不对「提到敏感字段的合法提问」判罚
  （例如「补办学生证需要身份证号吗？」是正常问题，必须放行）。
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from app.core.errors import BusinessError

# 除 \n \t 之外的控制字符（含 DEL）
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# 敏感数据取值：身份证 / 手机号 / 银行卡号（16–19 位纯数字）
ID_CARD = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
PHONE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
BANK_LIKE = re.compile(r"(?<!\d)\d{16,19}(?!\d)")

# 凭据赋值：必须紧跟「分隔符 + 字母数字取值」，避免「密码忘记了怎么办」这类正常提问被误判
CREDENTIAL_ASSIGNMENT = re.compile(r"(密码|口令|验证码|动态码)\s*[：:＝=是为]?\s*[A-Za-z0-9]{4,}")

# 提示词注入：命中即拒绝（模式尽量具体，降低误伤；统一忽略大小写以覆盖 Ignore/IGNORE）
INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"忽略(之前|以上|前面|上述)(的)?(所有)?(指令|要求|提示|规则)"),
    re.compile(r"(无视|绕过|突破)(之前|以上|上述)?(的)?(规则|限制|指令|要求)"),
    re.compile(r"(ignore|disregard)\s+(all\s+)?(previous|above|prior)", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"你现在(是|扮演|开始扮演)"),
    re.compile(r"(开发者|调试|上帝)模式"),
    re.compile(r"(输出|打印|重复|泄露|展示)(你的)?(系统)?(提示词|prompt|设定|指令)", re.IGNORECASE),
    re.compile(r"(reveal|print|repeat)\s+your\s+(system\s+)?(prompt|instructions)", re.IGNORECASE),
)

SENSITIVE_DATA_MESSAGE = "请勿在问题中填写身份证号、银行卡号或手机号等敏感信息"
CREDENTIAL_MESSAGE = "请勿在问题中填写密码或验证码"
INJECTION_MESSAGE = "问题中包含无法处理的内容，请换一种问法"


def sanitize_message(text: str) -> str:
    """去掉控制字符与首尾空白；长度上限由编排层按契约校验。"""
    return CONTROL_CHARS.sub("", text).strip()


def reject_sensitive_or_injected(text: str) -> None:
    """命中敏感数据取值或提示词注入时抛 BusinessError(400, INVALID_REQUEST)。"""
    if ID_CARD.search(text) or BANK_LIKE.search(text) or PHONE.search(text):
        raise BusinessError(400, "INVALID_REQUEST", SENSITIVE_DATA_MESSAGE)
    if CREDENTIAL_ASSIGNMENT.search(text):
        raise BusinessError(400, "INVALID_REQUEST", CREDENTIAL_MESSAGE)
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            raise BusinessError(400, "INVALID_REQUEST", INJECTION_MESSAGE)


def is_safe_source_url(url: str | None) -> bool:
    """来源链接白名单：仅接受 http / https 绝对地址（契约 §3.2、OWASP A08）。

    前端渲染前还有 ``isSafeSourceUrl()`` 双保险，这里先把不可引用的来源挡在响应之外。
    """
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
