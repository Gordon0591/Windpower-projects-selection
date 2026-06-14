from __future__ import annotations
"""字典接口"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import ProjectStatus, ProjectType, Province, TowerType
from schemas import DictItemOut, ListResponse, ProvinceOut, ProvincesGroupedOut

router = APIRouter(prefix="/dict", tags=["字典"])


@router.get("/provinces", response_model=ListResponse)
def list_provinces(db: Session = Depends(get_db)):
    """省份列表（按大区分组）"""
    provinces = db.execute(select(Province).order_by(Province.sort_order)).scalars().all()

    grouped: dict[str, list[ProvinceOut]] = {}
    for p in provinces:
        region = p.region
        if region not in grouped:
            grouped[region] = []
        grouped[region].append(ProvinceOut.model_validate(p))

    return ListResponse(data=[
        ProvincesGroupedOut(region=region, provinces=items)
        for region, items in grouped.items()
    ])


@router.get("/project-types", response_model=ListResponse)
def list_project_types(db: Session = Depends(get_db)):
    result = db.execute(select(ProjectType)).scalars().all()
    return ListResponse(data=[DictItemOut.model_validate(r) for r in result])


@router.get("/statuses", response_model=ListResponse)
def list_statuses(db: Session = Depends(get_db)):
    result = db.execute(select(ProjectStatus).order_by(ProjectStatus.sort_order)).scalars().all()
    return ListResponse(data=[DictItemOut.model_validate(r) for r in result])


@router.get("/tower-types", response_model=ListResponse)
def list_tower_types(db: Session = Depends(get_db)):
    result = db.execute(select(TowerType)).scalars().all()
    return ListResponse(data=[DictItemOut.model_validate(r) for r in result])
