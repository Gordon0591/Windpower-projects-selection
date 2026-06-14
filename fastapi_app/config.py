"""应用配置"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "风电项目信息收集系统"
    app_version: str = "0.1.0"

    # 数据库: 优先 PostgreSQL，否则自动降级为 SQLite（同步驱动，无需 greenlet）
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///wind_power.db",  # 默认 SQLite (pysqlite)，零依赖
    )

    default_page_size: int = 20
    max_page_size: int = 100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
