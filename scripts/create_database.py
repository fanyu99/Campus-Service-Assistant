import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings


def create_database(url: str | None = None) -> None:
    db_url = make_url(url if url is not None else get_settings().database_url)
    database = db_url.database
    if not database:
        print("连接串未包含数据库名，无法建库")
        raise SystemExit(1)
    if not db_url.drivername.startswith("mysql"):
        print(f"建库脚本仅支持 MySQL，当前连接串驱动为 {db_url.drivername}")
        raise SystemExit(1)
    server_url = db_url.set(database=None)
    engine = create_engine(server_url)
    try:
        with engine.connect() as connection:
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            connection.commit()
    except OperationalError:
        print("数据库服务器不可达，请检查连接配置与实例状态")
        raise SystemExit(1) from None
    finally:
        engine.dispose()
    print(f"数据库 {database} 已就绪（新建或已存在）")


if __name__ == "__main__":
    create_database()