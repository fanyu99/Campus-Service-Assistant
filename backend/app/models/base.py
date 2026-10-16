import enum
import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(referred_table_name)s_%(referred_column_0_name)s",
    "pk": "pk_%(table_name)s",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


_clock_lock = threading.Lock()
_last_now: datetime | None = None


def monotonic_utc_now() -> datetime:
    """严格单调递增的 UTC 时间戳。

    Windows 的 ``datetime.now()`` 粒度约 15.6ms，同一事务内连续落库的消息
    （用户问题 + 助手回复）会拿到**相同**时间戳，按 ``created_at`` 排序
    就不稳定。这里保证每次调用严格大于上一次（必要时补 1 微秒），
    使 ``created_at`` 始终能表达落库先后。
    """
    global _last_now
    with _clock_lock:
        now = datetime.now(timezone.utc)
        if _last_now is not None and now <= _last_now:
            now = _last_now + timedelta(microseconds=1)
        _last_now = now
        return now


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [m.value for m in enum_cls]


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)