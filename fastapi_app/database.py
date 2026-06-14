"""数据库连接管理（同步模式，兼容 Python 3.9 无需 greenlet）"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings

# SQLite 需要 check_same_thread=False
connect_args = {}
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(engine, class_=Session, expire_on_commit=False)

# 标记当前使用的数据库类型
IS_SQLITE = "sqlite" in settings.database_url


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
