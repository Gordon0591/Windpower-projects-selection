from __future__ import annotations
"""统计分析接口"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, extract, func, select, text
from sqlalchemy.orm import Session

from database import IS_SQLITE, get_db
from models import Project, ProjectStatus, TowerType

from schemas import (
    CapacityTrendItem,
    ListResponse,
    OverviewStats,
    ProvinceStat,
    StatusBreakdown,
    SupplierRankingItem,
    TowerBreakdown,
    TowerTypeRatioOut,
    TowerTypeRatioOverall,
    TowerTypeYearRatio,
    TypeBreakdown,
)

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/overview", response_model=ListResponse)
def overview(db: Session = Depends(get_db)):
    """数据总览面板"""
    this_year = date.today().year

    total = db.execute(select(
        func.count(Project.id),
        func.coalesce(func.sum(Project.capacity_mw), 0),
        func.coalesce(func.sum(Project.turbine_count), 0),
    )).one()
    total_projects, total_cap, total_turbines = total

    type_q = db.execute(select(
        func.coalesce(Project.project_type_id, 0),
        func.count(Project.id),
        func.coalesce(func.sum(Project.capacity_mw), 0),
    ).group_by(Project.project_type_id)).all()
    by_type = {}
    type_map = {1: "onshore", 2: "offshore"}
    for tid, cnt, cap in type_q:
        key = type_map.get(tid, "unknown")
        by_type[key] = TypeBreakdown(count=cnt or 0, capacity_mw=float(cap or 0))

    status_q = db.execute(
        select(ProjectStatus.code, func.count(Project.id),
               func.coalesce(func.sum(Project.capacity_mw), 0))
        .join(Project, Project.status_id == ProjectStatus.id, isouter=True)
        .group_by(ProjectStatus.code)
    ).all()
    by_status = {}
    for code, cnt, cap in status_q:
        by_status[code] = StatusBreakdown(count=cnt or 0, capacity_mw=float(cap or 0))

    tower_q = db.execute(
        select(TowerType.code, func.count(Project.id),
               func.coalesce(func.sum(Project.capacity_mw), 0))
        .join(Project, Project.tower_type_id == TowerType.id, isouter=True)
        .group_by(TowerType.code)
    ).all()
    by_tower = {}
    for code, cnt, cap in tower_q:
        by_tower[code] = TowerBreakdown(count=cnt or 0, capacity_mw=float(cap or 0))

    new_approved = float(db.execute(select(
        func.coalesce(func.sum(Project.capacity_mw), 0),
    ).where(extract("year", Project.approval_date) == this_year)).scalar() or 0)

    new_construction = float(db.execute(select(
        func.coalesce(func.sum(Project.capacity_mw), 0),
    ).where(extract("year", Project.construction_start_date) == this_year)).scalar() or 0)

    new_completed = float(db.execute(select(
        func.coalesce(func.sum(Project.capacity_mw), 0),
    ).where(extract("year", Project.completion_date) == this_year)).scalar() or 0)

    return ListResponse(data=OverviewStats(
        total_projects=total_projects or 0,
        total_capacity_mw=float(total_cap or 0),
        total_turbines=total_turbines or 0,
        by_type=by_type, by_status=by_status, by_tower_type=by_tower,
        this_year={
            "new_approved_mw": new_approved,
            "new_construction_mw": new_construction,
            "new_completed_mw": new_completed,
        },
    ))


@router.get("/by-province", response_model=ListResponse)
def stats_by_province(
    project_type: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """各省统计"""
    conditions = []
    if project_type:
        conditions.append(f"pt.code = '{project_type}'")
    if status:
        conditions.append(f"ps.code = '{status}'")

    from_clause = """
        FROM projects p
        JOIN provinces prov ON p.province_id = prov.id
        JOIN project_types pt ON p.project_type_id = pt.id
        JOIN project_statuses ps ON p.status_id = ps.id
    """
    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    if IS_SQLITE:
        sql = text(f"""
            SELECT prov.id, prov.name, prov.region,
                COUNT(p.id) AS project_count,
                COALESCE(SUM(p.capacity_mw), 0) AS total_capacity_mw,
                COALESCE(SUM(p.turbine_count), 0) AS total_turbines,
                COALESCE(SUM(CASE WHEN pt.code = 'onshore' THEN p.capacity_mw END), 0) AS onshore_mw,
                COALESCE(SUM(CASE WHEN pt.code = 'offshore' THEN p.capacity_mw END), 0) AS offshore_mw
            {from_clause} {where_clause}
            GROUP BY prov.id, prov.name, prov.region
            ORDER BY total_capacity_mw DESC
        """)
    else:
        sql = text(f"""
            SELECT prov.id, prov.name, prov.region,
                COUNT(p.id) AS project_count,
                COALESCE(SUM(p.capacity_mw), 0) AS total_capacity_mw,
                COALESCE(SUM(p.turbine_count), 0) AS total_turbines,
                COALESCE(SUM(p.capacity_mw) FILTER (WHERE pt.code = 'onshore'), 0) AS onshore_mw,
                COALESCE(SUM(p.capacity_mw) FILTER (WHERE pt.code = 'offshore'), 0) AS offshore_mw
            {from_clause} {where_clause}
            GROUP BY prov.id, prov.name, prov.region
            ORDER BY total_capacity_mw DESC
        """)
    rows = db.execute(sql).mappings().all()

    return ListResponse(data=[
        ProvinceStat(
            province_id=r["id"], province_name=r["name"], province_region=r["region"],
            project_count=r["project_count"], total_capacity_mw=float(r["total_capacity_mw"]),
            total_turbines=r["total_turbines"],
            onshore_mw=float(r["onshore_mw"]), offshore_mw=float(r["offshore_mw"]),
        ) for r in rows
    ])


@router.get("/capacity-trend", response_model=ListResponse)
def capacity_trend(
    granularity: str = Query("year", pattern="^(year|month)$"),
    metric: str = Query("approved", pattern="^(approved|construction_started|completed)$"),
    project_type: str | None = Query(None),
    year_from: int | None = Query(None),
    year_to: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """容量趋势"""
    metric_col = {
        "approved": "approval_date",
        "construction_started": "construction_start_date",
        "completed": "completion_date",
    }[metric]

    if IS_SQLITE:
        year_expr = f"CAST(strftime('%Y', p.{metric_col}) AS INTEGER)"
        month_expr = f"CAST(strftime('%m', p.{metric_col}) AS INTEGER)"
    else:
        year_expr = f"EXTRACT(YEAR FROM p.{metric_col})::INT"
        month_expr = f"EXTRACT(MONTH FROM p.{metric_col})::INT"

    conditions = [f"p.{metric_col} IS NOT NULL"]
    if project_type:
        conditions.append(f"pt.code = '{project_type}'")
    if year_from:
        conditions.append(f"{year_expr} >= {year_from}")
    if year_to:
        conditions.append(f"{year_expr} <= {year_to}")

    where_clause = "WHERE " + " AND ".join(conditions)

    if granularity == "month":
        group_cols = f"{year_expr}, {month_expr}"
        select_cols = f"{year_expr} AS year, {month_expr} AS month,"
        order_cols = "year, month"
    else:
        group_cols = year_expr
        select_cols = f"{year_expr} AS year, NULL AS month,"
        order_cols = "year"

    onshore_agg = "COALESCE(SUM(CASE WHEN pt.code = 'onshore' THEN p.capacity_mw END), 0)" if IS_SQLITE else "COALESCE(SUM(p.capacity_mw) FILTER (WHERE pt.code = 'onshore'), 0)"
    offshore_agg = "COALESCE(SUM(CASE WHEN pt.code = 'offshore' THEN p.capacity_mw END), 0)" if IS_SQLITE else "COALESCE(SUM(p.capacity_mw) FILTER (WHERE pt.code = 'offshore'), 0)"

    sql = text(f"""
        SELECT {select_cols}
            COUNT(p.id) AS project_count,
            COALESCE(SUM(p.capacity_mw), 0) AS capacity_mw,
            {onshore_agg} AS onshore_mw,
            {offshore_agg} AS offshore_mw
        FROM projects p
        JOIN project_types pt ON p.project_type_id = pt.id
        {where_clause}
        GROUP BY {group_cols}
        ORDER BY {order_cols}
    """)
    rows = db.execute(sql).mappings().all()

    return ListResponse(data=[
        CapacityTrendItem(
            year=r["year"], month=r.get("month"),
            capacity_mw=float(r["capacity_mw"]),
            onshore_mw=float(r["onshore_mw"]),
            offshore_mw=float(r["offshore_mw"]),
        ) for r in rows
    ])


@router.get("/tower-type-ratio", response_model=ListResponse)
def tower_type_ratio(db: Session = Depends(get_db)):
    """塔筒构造分布 & 年度趋势"""
    total = db.execute(select(func.count(Project.id))).scalar() or 1
    steel = db.execute(select(func.count(Project.id)).where(Project.tower_type_id == 1)).scalar() or 0
    hybrid = db.execute(select(func.count(Project.id)).where(Project.tower_type_id == 2)).scalar() or 0
    unknown = db.execute(select(func.count(Project.id)).where(Project.tower_type_id == 3)).scalar() or 0

    overall = TowerTypeRatioOverall(
        steel_pct=round(steel / total * 100, 1),
        hybrid_pct=round(hybrid / total * 100, 1),
        unknown_pct=round(unknown / total * 100, 1),
    )

    if IS_SQLITE:
        sql = text("""
            SELECT CAST(strftime('%Y', p.approval_date) AS INTEGER) AS year,
                COUNT(p.id) AS total,
                COUNT(CASE WHEN p.tower_type_id = 1 THEN 1 END) AS steel_count,
                COUNT(CASE WHEN p.tower_type_id = 2 THEN 1 END) AS hybrid_count,
                COUNT(CASE WHEN p.tower_type_id = 3 THEN 1 END) AS unknown_count
            FROM projects p WHERE p.approval_date IS NOT NULL
            GROUP BY CAST(strftime('%Y', p.approval_date) AS INTEGER)
            ORDER BY year
        """)
    else:
        sql = text("""
            SELECT EXTRACT(YEAR FROM p.approval_date)::INT AS year,
                COUNT(p.id) AS total,
                COUNT(p.id) FILTER (WHERE p.tower_type_id = 1) AS steel_count,
                COUNT(p.id) FILTER (WHERE p.tower_type_id = 2) AS hybrid_count,
                COUNT(p.id) FILTER (WHERE p.tower_type_id = 3) AS unknown_count
            FROM projects p WHERE p.approval_date IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM p.approval_date)
            ORDER BY year
        """)
    rows = db.execute(sql).mappings().all()

    by_year = []
    for r in rows:
        t = r["total"] or 1
        by_year.append(TowerTypeYearRatio(
            year=r["year"],
            steel_pct=round((r["steel_count"] or 0) / t * 100, 1),
            hybrid_pct=round((r["hybrid_count"] or 0) / t * 100, 1),
            unknown_pct=round((r["unknown_count"] or 0) / t * 100, 1),
        ))

    return ListResponse(data=TowerTypeRatioOut(overall=overall, by_year=by_year).model_dump())


@router.get("/supplier-ranking", response_model=ListResponse)
def supplier_ranking(db: Session = Depends(get_db)):
    """供应商排名"""
    sql = text("""
        SELECT turbine_supplier AS supplier,
            COUNT(*) AS project_count,
            COALESCE(SUM(capacity_mw), 0) AS total_capacity_mw,
            COALESCE(SUM(turbine_count), 0) AS total_turbines
        FROM projects
        WHERE turbine_supplier IS NOT NULL AND turbine_supplier != ''
        GROUP BY turbine_supplier
        ORDER BY total_capacity_mw DESC
        LIMIT 20
    """)
    rows = db.execute(sql).mappings().all()

    return ListResponse(data=[
        SupplierRankingItem(
            supplier=r["supplier"], project_count=r["project_count"],
            total_capacity_mw=float(r["total_capacity_mw"]),
            total_turbines=r["total_turbines"],
        ) for r in rows
    ])
