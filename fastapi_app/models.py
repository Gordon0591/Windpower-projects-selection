"""SQLAlchemy ORM 模型 — 与 schema.sql 一一对应"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── 字典表 ──────────────────────────────────────────────

class Province(Base):
    __tablename__ = "provinces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    region: Mapped[str] = mapped_column(String(10), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    projects: Mapped[list["Project"]] = relationship(back_populates="province")


class ProjectType(Base):
    __tablename__ = "project_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)

    projects: Mapped[list["Project"]] = relationship(back_populates="project_type")


class ProjectStatus(Base):
    __tablename__ = "project_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    projects: Mapped[list["Project"]] = relationship(back_populates="status")


class TowerType(Base):
    __tablename__ = "tower_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)

    projects: Mapped[list["Project"]] = relationship(back_populates="tower_type")


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(200))
    scraper_module: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    scrape_interval_min: Mapped[int] = mapped_column(Integer, default=360)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── 核心业务表 ──────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("name", "province_id", name="uq_project"),
        CheckConstraint("capacity_mw > 0", name="ck_capacity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    province_id: Mapped[int] = mapped_column(ForeignKey("provinces.id"), nullable=False)
    project_type_id: Mapped[int] = mapped_column(ForeignKey("project_types.id"), nullable=False)
    capacity_mw: Mapped[float] = mapped_column(Numeric(9, 2), nullable=False)
    turbine_count: Mapped[Optional[int]] = mapped_column(Integer)
    unit_capacity_mw: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    tower_type_id: Mapped[int] = mapped_column(ForeignKey("tower_types.id"), default=3)
    status_id: Mapped[int] = mapped_column(ForeignKey("project_statuses.id"), nullable=False)
    owner: Mapped[Optional[str]] = mapped_column(String(300))
    turbine_supplier: Mapped[Optional[str]] = mapped_column(String(300))
    investment_bn: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    approval_date: Mapped[Optional[date]] = mapped_column(Date)
    bid_date: Mapped[Optional[date]] = mapped_column(Date)
    construction_start_date: Mapped[Optional[date]] = mapped_column(Date)
    completion_date: Mapped[Optional[date]] = mapped_column(Date)
    planned_cod_date: Mapped[Optional[date]] = mapped_column(Date)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 关系
    province: Mapped["Province"] = relationship(back_populates="projects")
    project_type: Mapped["ProjectType"] = relationship(back_populates="projects")
    status: Mapped["ProjectStatus"] = relationship(back_populates="projects")
    tower_type: Mapped["TowerType"] = relationship(back_populates="projects")
    sources: Mapped[list["ProjectSource"]] = relationship(back_populates="project")
    status_logs: Mapped[list["ProjectStatusLog"]] = relationship(back_populates="project", order_by="ProjectStatusLog.changed_at.desc()")


class ProjectSource(Base):
    __tablename__ = "project_sources"
    __table_args__ = (
        UniqueConstraint("project_id", "source_id", "source_url", name="uq_project_source_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="sources")
    source: Mapped["DataSource"] = relationship()


class ProjectStatusLog(Base):
    __tablename__ = "project_status_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    old_status_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project_statuses.id"))
    new_status_id: Mapped[int] = mapped_column(ForeignKey("project_statuses.id"), nullable=False)
    changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_id: Mapped[Optional[int]] = mapped_column(ForeignKey("data_sources.id"))
    remark: Mapped[Optional[str]] = mapped_column(String(500))

    project: Mapped["Project"] = relationship(back_populates="status_logs")
    old_status: Mapped[Optional["ProjectStatus"]] = relationship(foreign_keys=[old_status_id])
    new_status: Mapped["ProjectStatus"] = relationship(foreign_keys=[new_status_id])
    source: Mapped[Optional["DataSource"]] = relationship()


class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    items_scraped: Mapped[int] = mapped_column(Integer, default=0)
    items_new: Mapped[int] = mapped_column(Integer, default=0)
    items_updated: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(10), default="running")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

    data_source: Mapped["DataSource"] = relationship()
