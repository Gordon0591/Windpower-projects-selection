from __future__ import annotations
"""采集 Pipeline 编排 — 抓取 → 提取 → 校验 → 入库"""

import logging
from datetime import datetime
from typing import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    DataSource,
    Project,
    ProjectSource,
    ProjectStatus,
    ProjectStatusLog,
    Province,
    ProjectType,
    ScrapeLog,
    TowerType,
)
from scrapers.base import ScrapedArticle
from scrapers.llm_extractor import ExtractedProject, LLMExtractor

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
# 字段映射辅助
# ══════════════════════════════════════════════════════════

# 省份名称 → province_id 映射（运行时缓存）
PROVINCE_MAP: dict[str, int] = {}

# 状态码 → status_id
STATUS_MAP: dict[str, int] = {}

# 塔筒码 → tower_type_id
TOWER_MAP: dict[str, int] = {}


async def _load_dicts(db: AsyncSession):
    """加载字典表到内存缓存"""
    global PROVINCE_MAP, STATUS_MAP, TOWER_MAP

    if not PROVINCE_MAP:
        result = await db.execute(select(Province))
        PROVINCE_MAP = {p.name: p.id for p in result.scalars().all()}

    if not STATUS_MAP:
        result = await db.execute(select(ProjectStatus))
        STATUS_MAP = {s.code: s.id for s in result.scalars().all()}

    if not TOWER_MAP:
        result = await db.execute(select(TowerType))
        TOWER_MAP = {t.code: t.id for t in result.scalars().all()}


# ══════════════════════════════════════════════════════════
# 数据校验
# ══════════════════════════════════════════════════════════

def validate_extraction(ep: ExtractedProject) -> list[str]:
    """校验提取结果，返回问题列表（空列表 = 通过）"""
    issues = []

    if not ep.project_name or len(ep.project_name) < 4:
        issues.append("项目名称缺失或过短")

    # 类型强制转换（LLM 可能返回字符串类型的数字）
    def _to_num(v, to_int=False):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return int(v) if to_int else float(v)
        try:
            return int(v) if to_int else float(v)
        except (ValueError, TypeError):
            return None

    capacity_mw = _to_num(ep.capacity_mw)
    turbine_count = _to_num(ep.turbine_count, to_int=True)
    unit_capacity_mw = _to_num(ep.unit_capacity_mw)
    investment_bn = _to_num(ep.investment_bn)

    if capacity_mw is not None:
        if capacity_mw < 0:
            issues.append(f"容量异常: {capacity_mw}MW")
        elif capacity_mw > 20000:
            issues.append(f"容量过大(>20GW): {capacity_mw}MW")

    if turbine_count is not None:
        if turbine_count <= 0:
            issues.append(f"风机台数异常: {turbine_count}")
        elif turbine_count > 10000:
            issues.append(f"风机台数过大: {turbine_count}")

    if investment_bn is not None:
        if investment_bn <= 0:
            issues.append(f"投资金额异常: {investment_bn}亿元")
        elif investment_bn > 2000:
            issues.append(f"投资金额过大: {investment_bn}亿元")

    # 容量 = 台数 × 单机容量 的粗略校验（允许 20% 误差）
    if all(v is not None for v in [capacity_mw, turbine_count, unit_capacity_mw]):
        expected = turbine_count * unit_capacity_mw
        if expected > 0:
            diff_pct = abs(capacity_mw - expected) / expected
            if diff_pct > 0.2:
                issues.append(
                    f"容量不匹配: 总容量{ep.capacity_mw}MW vs "
                    f"{ep.turbine_count}台×{ep.unit_capacity_mw}MW={expected:.1f}MW"
                )

    return issues


# ══════════════════════════════════════════════════════════
# Pipeline
# ══════════════════════════════════════════════════════════

class ScrapePipeline:
    """
    采集 Pipeline

    流程:
      1. 爬虫 yield ScrapedArticle
      2. LLM 提取 → ExtractedProject
      3. 数据校验
      4. 省份匹配
      5. 去重 (检查同名+同省是否已存在)
      6. 新增项目 或 更新状态 → 写入 DB
    """

    def __init__(self, db_session_factory, extractor: LLMExtractor | None = None):
        self._db_factory = db_session_factory
        self.extractor = extractor or LLMExtractor()

    async def run(self, scraper) -> dict:
        """
        执行一次完整的采集流程

        参数:
            scraper: BaseScraper 子类实例

        返回:
            {"items_scraped": N, "items_new": N, "items_updated": N, "items_skipped": N}
        """
        stats = {"items_scraped": 0, "items_new": 0, "items_updated": 0, "items_skipped": 0}

        # 创建采集日志
        async with self._db_factory() as db:
            await _load_dicts(db)

            scrape_log = ScrapeLog(
                data_source_id=scraper.source_id,
                started_at=datetime.now(),
                status="running",
            )
            db.add(scrape_log)
            await db.commit()

        try:
            async for article in scraper.scrape():
                stats["items_scraped"] += 1
                logger.info(f"[{stats['items_scraped']}] {article.title[:60]}...")

                # ── Step 1: LLM 提取 ──
                extracted = await self.extractor.extract(article.content, article.title)

                if not extracted.has_project:
                    stats["items_skipped"] += 1
                    logger.debug(f"  → 无项目信息，跳过")
                    continue

                # ── Step 2: 数据校验 ──
                issues = validate_extraction(extracted)
                if issues:
                    logger.warning(f"  → 校验警告: {'; '.join(issues)}")
                    # 有严重问题时跳过，小问题继续
                    if any("缺失" in i or "异常" in i for i in issues):
                        stats["items_skipped"] += 1
                        continue

                # ── Step 3: 省份匹配 ──
                province_id = self._match_province(extracted.province)
                if not province_id:
                    logger.warning(f"  → 无法匹配省份: {extracted.province}，使用'未知'")
                    province_id = PROVINCE_MAP.get("未知", 94)  # fallback

                # ── Step 4: 入库 ──
                async with self._db_factory() as db:
                    result = await self._upsert_project(
                        db, extracted, province_id, article, scraper.source_id
                    )
                    await db.commit()

                if result == "new":
                    stats["items_new"] += 1
                    logger.info(f"  ✅ 新增: {extracted.project_name}")
                elif result == "updated":
                    stats["items_updated"] += 1
                    logger.info(f"  🔄 更新: {extracted.project_name}")
                else:
                    stats["items_skipped"] += 1
                    logger.info(f"  ⏭️ 跳过(重复): {extracted.project_name}")

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
        finally:
            # 更新采集日志
            async with self._db_factory() as db:
                log = await db.get(ScrapeLog, scrape_log.id)
                if log:
                    log.finished_at = datetime.now()
                    log.items_scraped = stats["items_scraped"]
                    log.items_new = stats["items_new"]
                    log.items_updated = stats["items_updated"]
                    log.status = "success"
                    await db.commit()

            await scraper.close()

        return stats

    # ── 内部方法 ─────────────────────────────────────────

    @staticmethod
    def _match_province(province_name: str | None) -> int | None:
        """模糊匹配省份名称 → ID"""
        if not province_name:
            return None

        # 精确匹配
        if province_name in PROVINCE_MAP:
            return PROVINCE_MAP[province_name]

        # 模糊匹配（名称包含关系）
        for name, pid in PROVINCE_MAP.items():
            if name in province_name or province_name in name:
                return pid

        return None

    @staticmethod
    def _parse_date(date_str: str | None) -> datetime.date | None:
        """解析日期字符串 → date 对象"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except (ValueError, IndexError):
            return None

    async def _upsert_project(
        self,
        db: AsyncSession,
        ep: ExtractedProject,
        province_id: int,
        article: ScrapedArticle,
        source_id: int,
    ) -> str:
        """
        插入或更新项目

        去重策略: name + province_id 唯一键
        - 不存在 → INSERT + status_log + source 关联
        - 已存在 → 检查是否有新信息可补充（状态变更/新字段）
        """
        # 查是否已存在
        result = await db.execute(
            select(Project).where(
                Project.name == ep.project_name,
                Project.province_id == province_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            # ── 新增项目 ──
            type_id = 1  # 默认陆上
            if ep.project_type == "offshore":
                type_id = 2

            status_id = STATUS_MAP.get(ep.status, STATUS_MAP.get("planned", 2))
            tower_id = TOWER_MAP.get(ep.tower_type, 3)

            # 安全转换数值（LLM 可能返回字符串）
            def _safe_num(v, to_int=False):
                if v is None: return None
                if isinstance(v, (int, float)): return int(v) if to_int else float(v)
                try: return int(v) if to_int else float(v)
                except (ValueError, TypeError): return None

            project = Project(
                name=ep.project_name,
                province_id=province_id,
                project_type_id=type_id,
                capacity_mw=_safe_num(ep.capacity_mw) or 0,
                turbine_count=_safe_num(ep.turbine_count, to_int=True),
                unit_capacity_mw=_safe_num(ep.unit_capacity_mw),
                tower_type_id=tower_id,
                status_id=status_id,
                owner=ep.owner,
                turbine_supplier=ep.turbine_supplier,
                investment_bn=_safe_num(ep.investment_bn),
                approval_date=self._parse_date(ep.approval_date),
                bid_date=self._parse_date(ep.bid_date),
                construction_start_date=self._parse_date(ep.construction_start_date),
                completion_date=self._parse_date(ep.completion_date),
                planned_cod_date=self._parse_date(ep.planned_cod_date),
                description=f"来源: {article.source_name} ({article.publish_date.strftime('%Y-%m-%d') if article.publish_date else '未知日期'})",
                is_verified=False,
            )
            db.add(project)
            await db.flush()

            # 状态变更日志
            db.add(ProjectStatusLog(
                project_id=project.id,
                new_status_id=status_id,
                changed_at=article.publish_date or datetime.now(),
                source_id=source_id,
                remark=f"自动采集自 {article.source_name}",
            ))

            # 来源关联
            db.add(ProjectSource(
                project_id=project.id,
                source_id=source_id,
                source_url=article.url,
            ))

            return "new"

        else:
            # ── 更新已有项目 ──
            updated = False

            # 补充空字段
            for field_name, ep_value in [
                ("turbine_count", ep.turbine_count),
                ("unit_capacity_mw", ep.unit_capacity_mw),
                ("investment_bn", ep.investment_bn),
                ("owner", ep.owner),
                ("turbine_supplier", ep.turbine_supplier),
                ("description", None),
            ]:
                if field_name == "description":
                    continue
                existing_val = getattr(existing, field_name)
                if existing_val is None and ep_value is not None:
                    setattr(existing, field_name, ep_value)
                    updated = True

            # 塔筒类型补充
            if existing.tower_type_id == 3 and ep.tower_type:  # 3 = 待确认
                new_tower_id = TOWER_MAP.get(ep.tower_type)
                if new_tower_id and new_tower_id != 3:
                    existing.tower_type_id = new_tower_id
                    updated = True

            # 日期补充
            for field_name, ep_date_str in [
                ("approval_date", ep.approval_date),
                ("bid_date", ep.bid_date),
                ("construction_start_date", ep.construction_start_date),
                ("completion_date", ep.completion_date),
                ("planned_cod_date", ep.planned_cod_date),
            ]:
                existing_date = getattr(existing, field_name)
                if existing_date is None and ep_date_str:
                    parsed = self._parse_date(ep_date_str)
                    if parsed:
                        setattr(existing, field_name, parsed)
                        updated = True

            # 状态推进（仅当新状态在生命周期上更靠后时更新）
            if ep.status:
                new_status_id = STATUS_MAP.get(ep.status)
                if new_status_id:
                    # 简单规则：sort_order 大的更靠后
                    old_sort = 0
                    new_sort = 0
                    for code, sid in STATUS_MAP.items():
                        if sid == existing.status_id:
                            old_sort = sid  # 用 ID 近似判断
                    if new_status_id > existing.status_id:  # 简化判断
                        old_status_id = existing.status_id
                        existing.status_id = new_status_id
                        updated = True

                        db.add(ProjectStatusLog(
                            project_id=existing.id,
                            old_status_id=old_status_id,
                            new_status_id=new_status_id,
                            changed_at=article.publish_date or datetime.now(),
                            source_id=source_id,
                            remark=f"状态变更: {article.source_name}",
                        ))

            # 添加新的来源关联（如果 URL 不同）
            existing_source = await db.execute(
                select(ProjectSource).where(
                    ProjectSource.project_id == existing.id,
                    ProjectSource.source_url == article.url,
                )
            )
            if not existing_source.scalar_one_or_none():
                db.add(ProjectSource(
                    project_id=existing.id,
                    source_id=source_id,
                    source_url=article.url,
                ))

            return "updated" if updated else "skipped"
