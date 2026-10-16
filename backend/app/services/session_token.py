"""匿名会话标识的规范化。

写入（问答创建会话）与读取（最近记录查询）必须用同一套规则，
否则客户端发送超长 token 时会出现「写得进去、查不出来」的不对称问题。
"""

SESSION_TOKEN_MAX_LENGTH = 64


def normalize_session_token(value: str | None) -> str | None:
    """去空白 + 截断到列长度；空白字符串视为未提供。"""
    if value is None:
        return None
    token = value.strip()
    if not token:
        return None
    return token[:SESSION_TOKEN_MAX_LENGTH]
