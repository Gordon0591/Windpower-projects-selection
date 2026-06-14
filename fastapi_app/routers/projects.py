from __future__ import annotations
"""项目 CRUD 接口"""

import math
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from config import settings
from database import IS_SQLITE, get_db
from models import (
    DataSource,
    Project,
    ProjectSource,
    ProjectStatus,
    ProjectStatusLog,
    Province,
    ProjectType,
    TowerType,
)
from schemas import (
    ListResponse,
    Pagination,
    ProjectCreate,
    ProjectDetail,
    ProjectListItem,
    ProjectSortBy,
    ProjectSourceOut,
    ProjectStatusUpdate,
    ProjectUpdate,
    SortOrder,
    StatusLogOut,
)

router = APIRouter(prefix="/projects", tags=["项目"])


# ── 辅助：构建查询条件 ──────────────────────────────────

def _build_filters(
    province_id: int | None = None,
    region: str | None = None,
    project_type: str | None = None,
    status: str | None = None,
    tower_type: str | None = None,
    capacity_min: float | None = None,
    capacity_max: float | None = None,
    approval_date_from: date | None = None,
    approval_date_to: date | None = None,
    completion_date_from: date | None = None,
    completion_date_to: date | None = None,
    owner: str | None = None,
    supplier: str | None = None,
    keyword: str | None = None,
):
    conditions = []

    if province_id is not None:
        conditions.append(Project.province_id == province_id)
    if region is not None:
        conditions.append(Province.region == region)
    if project_type is not None:
        conditions.append(ProjectType.code == project_type)
    if status is not None:
        conditions.append(ProjectStatus.code == status)
    if tower_type is not None:
        conditions.append(TowerType.code == tower_type)
    if capacity_min is not None:
        conditions.append(Project.capacity_mw >= capacity_min)
    if capacity_max is not None:
        conditions.append(Project.capacity_mw <= capacity_max)
    if approval_date_from is not None:
        conditions.append(Project.approval_date >= approval_date_from)
    if approval_date_to is not None:
        conditions.append(Project.approval_date <= approval_date_to)
    if completion_date_from is not None:
        conditions.append(Project.completion_date >= completion_date_from)
    if completion_date_to is not None:
        conditions.append(Project.completion_date <= completion_date_to)
    if owner is not None:
        conditions.append(Project.owner.ilike(f"%{owner}%"))
    if supplier is not None:
        conditions.append(Project.turbine_supplier.ilike(f"%{supplier}%"))
    if keyword is not None:
        if IS_SQLITE:
            like_pat = f"%{keyword}%"
            conditions.append(
                or_(
                    Project.name.ilike(like_pat),
                    Project.owner.ilike(like_pat),
                    Project.turbine_supplier.ilike(like_pat),
                    Project.description.ilike(like_pat),
                )
            )
        else:
            ts_query = func.to_tsquery("simple", " & ".join(keyword.split()))
            conditions.append(
                func.to_tsvector(
                    "simple",
                    func.coalesce(Project.name, "")
                    .op("||")(" ")
                    .op("||")(func.coalesce(Project.owner, ""))
                    .op("||")(" ")
                    .op("||")(func.coalesce(Project.turbine_supplier, ""))
                    .op("||")(" ")
                    .op("||")(func.coalesce(Project.description, "")),
                ).op("@@")(ts_query)
            )

    return conditions


# ── 接口 ────────────────────────────────────────────────

@router.get("", response_model=ListResponse)
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    province_id: int | None = Query(None),
    region: str | None = Query(None),
    project_type: str | None = Query(None),
    status: str | None = Query(None),
    tower_type: str | None = Query(None),
    capacity_min: float | None = Query(None, gt=0),
    capacity_max: float | None = Query(None, gt=0),
    approval_date_from: date | None = Query(None),
    approval_date_to: date | None = Query(None),
    completion_date_from: date | None = Query(None),
    completion_date_to: date | None = Query(None),
    owner: str | None = Query(None),
    supplier: str | None = Query(None),
    keyword: str | None = Query(None),
    sort_by: ProjectSortBy = Query(ProjectSortBy.updated_at),
    sort_order: SortOrder = Query(SortOrder.desc),
    db: Session = Depends(get_db),
):
    """项目列表（支持多维筛选 + 全文搜索）"""
    base = (
        select(Project)
        .join(Project.province)
        .join(Project.project_type)
        .join(Project.status)
        .join(Project.tower_type)
    )

    conditions = _build_filters(
        province_id=province_id, region=region, project_type=project_type,
        status=status, tower_type=tower_type,
        capacity_min=capacity_min, capacity_max=capacity_max,
        approval_date_from=approval_date_from, approval_date_to=approval_date_to,
        completion_date_from=completion_date_from, completion_date_to=completion_date_to,
        owner=owner, supplier=supplier, keyword=keyword,
    )
    if conditions:
        base = base.where(and_(*conditions))

    count_q = select(func.count()).select_from(base.subquery())
    total = db.execute(count_q).scalar() or 0

    sort_col = getattr(Project, sort_by.value)
    if sort_order == SortOrder.desc:
        sort_col = sort_col.desc()

    q = (
        base.options(
            joinedload(Project.province),
            joinedload(Project.project_type),
            joinedload(Project.status),
            joinedload(Project.tower_type),
        )
        .order_by(sort_col)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    projects = db.execute(q).unique().scalars().all()

    return ListResponse(
        data=[ProjectListItem.model_validate(p) for p in projects],
        pagination=Pagination(
            page=page, page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        ),
    )


@router.get("/{project_id}", response_model=ListResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """项目详情"""
    q = (
        select(Project)
        .options(
            joinedload(Project.province),
            joinedload(Project.project_type),
            joinedload(Project.status),
            joinedload(Project.tower_type),
            selectinload(Project.status_logs).joinedload(ProjectStatusLog.old_status),
            selectinload(Project.status_logs).joinedload(ProjectStatusLog.new_status),
            selectinload(Project.sources).joinedload(ProjectSource.source),
        )
        .where(Project.id == project_id)
    )
    project = db.execute(q).unique().scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    history = []
    for log in project.status_logs:
        history.append(StatusLogOut(
            from_status=log.old_status.name if log.old_status else None,
            to_status=log.new_status.name,
            changed_at=log.changed_at or log.changed_at,
            remark=log.remark,
        ))

    sources = []
    for ps in project.sources:
        sources.append(ProjectSourceOut(
            source_name=ps.source.name if ps.source else "未知来源",
            source_url=ps.source_url,
            captured_at=ps.captured_at,
        ))

    # 手动构造 detail（避免 model_validate 自动映射 nested relationships 失败）
    detail = ProjectDetail(
        id=project.id,
        name=project.name,
        province=project.province,
        project_type=project.project_type,
        capacity_mw=project.capacity_mw,
        turbine_count=project.turbine_count,
        unit_capacity_mw=project.unit_capacity_mw,
        tower_type=project.tower_type,
        status=project.status,
        owner=project.owner,
        turbine_supplier=project.turbine_supplier,
        investment_bn=project.investment_bn,
        approval_date=project.approval_date,
        bid_date=project.bid_date,
        construction_start_date=project.construction_start_date,
        completion_date=project.completion_date,
        planned_cod_date=project.planned_cod_date,
        description=project.description,
        is_verified=project.is_verified,
        created_at=project.created_at,
        updated_at=project.updated_at,
        status_history=history,
        sources=sources,
    )

    return ListResponse(data=detail)


@router.post("", response_model=ListResponse, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    """手动新增项目"""
    existing = db.execute(
        select(Project).where(
            Project.name == body.name, Project.province_id == body.province_id
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="同名项目在该省份已存在")

    project = Project(
        name=body.name, province_id=body.province_id,
        project_type_id=body.project_type_id,
        capacity_mw=body.capacity_mw,
        turbine_count=body.turbine_count,
        unit_capacity_mw=body.unit_capacity_mw,
        tower_type_id=body.tower_type_id,
        status_id=body.status_id,
        owner=body.owner, turbine_supplier=body.turbine_supplier,
        investment_bn=body.investment_bn,
        approval_date=body.approval_date, bid_date=body.bid_date,
        construction_start_date=body.construction_start_date,
        completion_date=body.completion_date,
        planned_cod_date=body.planned_cod_date,
        description=body.description,
        is_verified=True,
    )
    db.add(project)
    db.flush()

    db.add(ProjectStatusLog(
        project_id=project.id, new_status_id=body.status_id,
        changed_at=datetime.now(), remark="手动创建项目",
    ))

    db.commit()
    db.refresh(project)

    return ListResponse(data=ProjectDetail.model_validate(project))


@router.put("/{project_id}", response_model=ListResponse)
def update_project(project_id: int, body: ProjectUpdate, db: Session = Depends(get_db)):
    """更新项目"""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return ListResponse(data=ProjectDetail.model_validate(project))


@router.patch("/{project_id}/status", response_model=ListResponse)
def update_project_status(project_id: int, body: ProjectStatusUpdate, db: Session = Depends(get_db)):
    """更新项目状态"""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    old_status_id = project.status_id
    project.status_id = body.status_id

    db.add(ProjectStatusLog(
        project_id=project.id,
        old_status_id=old_status_id,
        new_status_id=body.status_id,
        changed_at=body.changed_at or datetime.now(),
        source_id=body.source_id,
        remark=body.remark,
    ))

    db.commit()
    db.refresh(project)

    return ListResponse(data=ProjectDetail.model_validate(project))
