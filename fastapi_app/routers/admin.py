from __future__ import annotations
"""管理后台接口"""

import math
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from database import get_db
from models import DataSource, ProjectSource, ScrapeLog
from schemas import DataSourceDetail, ListResponse, Pagination, ScrapeLogItem

router = APIRouter(prefix="/admin", tags=["管理"])


@router.get("/data-sources", response_model=ListResponse)
def list_data_sources(db: Session = Depends(get_db)):
    sources = db.execute(select(DataSource).order_by(DataSource.id)).scalars().all()

    data = []
    for s in sources:
        last = db.execute(
            select(ScrapeLog)
            .where(ScrapeLog.data_source_id == s.id)
            .order_by(ScrapeLog.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        total_captured = db.execute(
            select(func.count(ProjectSource.id)).where(ProjectSource.source_id == s.id)
        ).scalar() or 0

        data.append(DataSourceDetail(
            id=s.id, name=s.name, type=s.type, base_url=s.base_url,
            is_active=s.is_active, scrape_interval_min=s.scrape_interval_min,
            last_run=last.started_at if last else None,
            last_status=last.status if last else None,
            last_items=last.items_scraped if last else None,
            total_captured=total_captured,
        ))

    return ListResponse(data=data)


@router.get("/scrape-logs", response_model=ListResponse)
def list_scrape_logs(
    source_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    conditions = []
    if source_id is not None:
        conditions.append(ScrapeLog.data_source_id == source_id)
    if date_from is not None:
        conditions.append(func.date(ScrapeLog.started_at) >= date_from)
    if date_to is not None:
        conditions.append(func.date(ScrapeLog.started_at) <= date_to)
    if status is not None:
        conditions.append(ScrapeLog.status == status)

    base = select(ScrapeLog)
    if conditions:
        base = base.where(and_(*conditions))

    count_q = select(func.count()).select_from(base.subquery())
    total = db.execute(count_q).scalar() or 0

    logs = db.execute(
        base.order_by(ScrapeLog.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    source_ids = list({log.data_source_id for log in logs})
    source_map = {}
    if source_ids:
        for s in db.execute(select(DataSource).where(DataSource.id.in_(source_ids))).scalars().all():
            source_map[s.id] = s.name

    return ListResponse(
        data=[ScrapeLogItem(
            id=log.id, data_source_id=log.data_source_id,
            data_source_name=source_map.get(log.data_source_id),
            started_at=log.started_at, finished_at=log.finished_at,
            items_scraped=log.items_scraped, items_new=log.items_new,
            items_updated=log.items_updated,
            status=log.status, error_message=log.error_message,
        ) for log in logs],
        pagination=Pagination(page=page, page_size=page_size, total=total,
            total_pages=math.ceil(total / page_size) if total > 0 else 0),
    )
