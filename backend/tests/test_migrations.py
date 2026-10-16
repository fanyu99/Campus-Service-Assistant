import sqlalchemy as sa
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.models import Base

ALL_TABLES = {
    "service_items",
    "source_documents",
    "conversations",
    "conversation_messages",
    "feedback",
}


def test_migration_roundtrip(alembic_cfg):
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    connection = engine.connect()
    alembic_cfg.attributes["connection"] = connection
    try:
        command.upgrade(alembic_cfg, "head")
        tables = set(sa.inspect(connection).get_table_names())
        assert ALL_TABLES <= tables

        command.downgrade(alembic_cfg, "base")
        tables = set(sa.inspect(connection).get_table_names())
        assert not ALL_TABLES & tables

        command.upgrade(alembic_cfg, "head")
        tables = set(sa.inspect(connection).get_table_names())
        assert ALL_TABLES <= tables
    finally:
        connection.close()
        engine.dispose()


def test_migration_version_after_upgrade(alembic_cfg):
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    connection = engine.connect()
    alembic_cfg.attributes["connection"] = connection
    try:
        command.upgrade(alembic_cfg, "head")
        current = sa.inspect(connection).get_table_names()
        assert "alembic_version" in current
        version = connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar()
        assert version == "0006"
    finally:
        connection.close()
        engine.dispose()


def test_models_and_migration_no_drift(db_engine):
    with db_engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diff = compare_metadata(context, Base.metadata)
        assert diff == []