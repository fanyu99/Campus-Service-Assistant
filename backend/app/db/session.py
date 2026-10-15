from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_db_engine(url: str | None = None) -> Engine:
    return create_engine(
        url if url is not None else get_settings().database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


_session_factory: sessionmaker[Session] | None = None


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(create_db_engine())
    return _session_factory


def get_db() -> Iterator[Session]:
    session = _get_session_factory()()
    try:
        yield session
    finally:
        session.close()