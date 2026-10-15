import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.config import get_settings
from app.db.session import create_session_factory, get_db
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def alembic_cfg() -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", "sqlite://")
    return cfg


@pytest.fixture
def db_engine(alembic_cfg: Config):
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.commit()
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "head")
        connection.commit()
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    session = create_session_factory(db_engine)()
    yield session
    session.close()


@pytest.fixture
def db_client(db_engine) -> TestClient:
    application = create_app()
    test_session_factory = create_session_factory(db_engine)

    def override_get_db() -> Iterator[Session]:
        session = test_session_factory()
        try:
            yield session
        finally:
            session.close()

    application.dependency_overrides[get_db] = override_get_db
    return TestClient(application)
