"""风电项目信息收集系统 — FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine
from models import Base
from routers import admin, dict, projects, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时自动建表 + 种子数据"""
    Base.metadata.create_all(bind=engine)
    from database import SessionLocal
    db = SessionLocal()
    try:
        from seed_data import seed
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/v1")
app.include_router(stats.router, prefix="/v1")
app.include_router(dict.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")


@app.get("/")
def root():
    return {"name": settings.app_name, "version": settings.app_version, "docs": "/docs"}
