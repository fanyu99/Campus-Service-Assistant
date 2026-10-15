from datetime import datetime, timezone
from typing import Annotated

from fastapi import Query
from pydantic import BeforeValidator


def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


UtcDateTime = Annotated[datetime, BeforeValidator(_normalize_utc)]

LimitParam = Annotated[int, Query(ge=1, le=50)]