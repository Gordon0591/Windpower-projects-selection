from __future__ import annotations
"""Pydantic 请求/响应模型"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


# ══════════════════════════════════════════════════════════
# 字典响应
# ══════════════════════════════════════════════════════════

class ProvinceOut(BaseModel):
    id: int
    name: str
    region: str

    model_config = {"from_attributes": True}


class ProvincesGroupedOut(BaseModel):
    """省份按大区分组"""
    region: str
    provinces: list[ProvinceOut]


class DictItemOut(BaseModel):
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════
# 项目响应
# ══════════════════════════════════════════════════════════

class ProjectStatusOut(BaseModel):
    code: str
    name: str

    model_config = {"from_attributes": True}


class ProjectListItem(BaseModel):
    """项目列表项（精简）"""
    id: int
    name: str
    province: ProvinceOut
    project_type: DictItemOut
    capacity_mw: float
    turbine_count: int | None = None
    unit_capacity_mw: float | None = None
    tower_type: DictItemOut
    status: DictItemOut
    owner: str | None = None
    turbine_supplier: str | None = None
    investment_bn: float | None = None
    approval_date: date | None = None
    construction_start_date: date | None = None
    planned_cod_date: date | None = None
    is_verified: bool = False
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class StatusLogOut(BaseModel):
    from_status: str | None = None
    to_status: str
    changed_at: datetime
    remark: str | None = None

    model_config = {"from_attributes": True}


class ProjectSourceOut(BaseModel):
    source_name: str
    source_url: str | None = None
    captured_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetail(BaseModel):
    """项目详情（完整字段 + 状态历史 + 来源列表）"""
    id: int
    name: str
    province: ProvinceOut
    project_type: DictItemOut
    capacity_mw: float
    turbine_count: int | None = None
    unit_capacity_mw: float | None = None
    tower_type: DictItemOut
    status: DictItemOut
    owner: str | None = None
    turbine_supplier: str | None = None
    investment_bn: float | None = None
    approval_date: date | None = None
    bid_date: date | None = None
    construction_start_date: date | None = None
    completion_date: date | None = None
    planned_cod_date: date | None = None
    description: str | None = None
    is_verified: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status_history: list[StatusLogOut] = []
    sources: list[ProjectSourceOut] = []

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════
# 项目请求
# ══════════════════════════════════════════════════════════

class ProjectCreate(BaseModel):
    """新增项目"""
    name: str = Field(..., max_length=300)
    province_id: int
    project_type_id: int
    capacity_mw: float = Field(..., gt=0)
    turbine_count: int | None = Field(default=None, gt=0)
    unit_capacity_mw: float | None = Field(default=None, gt=0)
    tower_type_id: int = 3
    status_id: int
    owner: str | None = Field(default=None, max_length=300)
    turbine_supplier: str | None = Field(default=None, max_length=300)
    investment_bn: float | None = Field(default=None, gt=0)
    approval_date: date | None = None
    bid_date: date | None = None
    construction_start_date: date | None = None
    completion_date: date | None = None
    planned_cod_date: date | None = None
    description: str | None = None
    source_url: str | None = Field(default=None, max_length=1000)


class ProjectUpdate(BaseModel):
    """更新项目（所有字段可选）"""
    name: str | None = Field(default=None, max_length=300)
    province_id: int | None = None
    project_type_id: int | None = None
    capacity_mw: float | None = Field(default=None, gt=0)
    turbine_count: int | None = Field(default=None, gt=0)
    unit_capacity_mw: float | None = Field(default=None, gt=0)
    tower_type_id: int | None = None
    status_id: int | None = None
    owner: str | None = Field(default=None, max_length=300)
    turbine_supplier: str | None = Field(default=None, max_length=300)
    investment_bn: float | None = Field(default=None, gt=0)
    approval_date: date | None = None
    bid_date: date | None = None
    construction_start_date: date | None = None
    completion_date: date | None = None
    planned_cod_date: date | None = None
    description: str | None = None
    is_verified: bool | None = None


class ProjectStatusUpdate(BaseModel):
    """更新项目状态"""
    status_id: int
    changed_at: datetime | None = None
    source_id: int | None = None
    remark: str | None = Field(default=None, max_length=500)


# ══════════════════════════════════════════════════════════
# 统计响应
# ══════════════════════════════════════════════════════════

class StatusBreakdown(BaseModel):
    count: int = 0
    capacity_mw: float = 0.0


class TypeBreakdown(BaseModel):
    count: int = 0
    capacity_mw: float = 0.0


class TowerBreakdown(BaseModel):
    count: int = 0
    capacity_mw: float = 0.0


class OverviewStats(BaseModel):
    total_projects: int = 0
    total_capacity_mw: float = 0.0
    total_turbines: int = 0
    by_type: dict[str, TypeBreakdown] = {}
    by_status: dict[str, StatusBreakdown] = {}
    by_tower_type: dict[str, TowerBreakdown] = {}
    this_year: dict[str, float] = {}


class ProvinceStat(BaseModel):
    province_id: int
    province_name: str
    province_region: str
    project_count: int = 0
    total_capacity_mw: float = 0.0
    total_turbines: int = 0
    onshore_mw: float = 0.0
    offshore_mw: float = 0.0


class CapacityTrendItem(BaseModel):
    year: int
    month: int | None = None
    capacity_mw: float = 0.0
    onshore_mw: float = 0.0
    offshore_mw: float = 0.0


class TowerTypeRatioOverall(BaseModel):
    steel_pct: float = 0.0
    hybrid_pct: float = 0.0
    unknown_pct: float = 0.0


class TowerTypeYearRatio(BaseModel):
    year: int
    steel_pct: float = 0.0
    hybrid_pct: float = 0.0
    unknown_pct: float = 0.0


class TowerTypeRatioOut(BaseModel):
    overall: TowerTypeRatioOverall
    by_year: list[TowerTypeYearRatio] = []


class SupplierRankingItem(BaseModel):
    supplier: str
    project_count: int = 0
    total_capacity_mw: float = 0.0
    total_turbines: int = 0


# ══════════════════════════════════════════════════════════
# 数据源 & 采集日志
# ══════════════════════════════════════════════════════════

class DataSourceOut(BaseModel):
    id: int
    name: str
    type: str
    is_active: bool
    scrape_interval_min: int

    model_config = {"from_attributes": True}


class DataSourceDetail(BaseModel):
    id: int
    name: str
    type: str
    base_url: str | None = None
    is_active: bool
    scrape_interval_min: int
    last_run: datetime | None = None
    last_status: str | None = None
    last_items: int | None = None
    total_captured: int = 0

    model_config = {"from_attributes": True}


class ScrapeLogItem(BaseModel):
    id: int
    data_source_id: int
    data_source_name: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    items_scraped: int = 0
    items_new: int = 0
    items_updated: int = 0
    status: str
    error_message: str | None = None

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════
# 通用
# ══════════════════════════════════════════════════════════

class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"


class ListResponse(ApiResponse):
    data: Any = None
    pagination: Pagination | None = None


class ProjectSortBy(str, Enum):
    capacity_mw = "capacity_mw"
    approval_date = "approval_date"
    construction_start_date = "construction_start_date"
    completion_date = "completion_date"
    created_at = "created_at"
    updated_at = "updated_at"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"
