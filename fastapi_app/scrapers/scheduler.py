from __future__ import annotations
"""采集调度器 — 定时触发各数据源爬虫"""

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models import DataSource
from scrapers.llm_extractor import LLMExtractor
from scrapers.pipeline import ScrapePipeline

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
# 爬虫注册表
# ══════════════════════════════════════════════════════════

from scrapers.bjx_scraper import BjxScraper

# source_id → Scraper 类
SCRAPER_REGISTRY: dict[int, type] = {
    1: BjxScraper,
    # 后续扩展:
    # 2: DailyWindScraper,
    # 3: OffshoreWatchScraper,
    # 4: CebpubScraper,
    # 5: TzxmScraper,
    # 6: NeaScraper,
}


# ══════════════════════════════════════════════════════════
# 调度器
# ══════════════════════════════════════════════════════════

class ScrapeScheduler:
    """
    采集调度器
    - 从 data_sources 表读取各数据源的采集间隔
    - 为每个启用的数据源注册定时任务
    - 支持手动触发
    """

    def __init__(
        self,
        db_factory: async_sessionmaker,
        extractor: LLMExtractor | None = None,
    ):
        self.db_factory = db_factory
        self.extractor = extractor or LLMExtractor()
        self.scheduler = AsyncIOScheduler()
        self._pipeline = ScrapePipeline(db_factory, self.extractor)

    async def setup(self):
        """从数据库加载数据源配置，注册定时任务"""
        async with self.db_factory() as db:
            result = await db.execute(
                select(DataSource).where(DataSource.is_active == True)
            )
            sources = result.scalars().all()

        for src in sources:
            if src.id not in SCRAPER_REGISTRY:
                logger.warning(f"数据源 [{src.id}] {src.name} 没有对应的爬虫实现，跳过")
                continue

            scraper_cls = SCRAPER_REGISTRY[src.id]
            interval_minutes = src.scrape_interval_min or 360

            self.scheduler.add_job(
                self._run_scraper,
                trigger="interval",
                minutes=interval_minutes,
                id=f"scraper_{src.id}",
                name=f"{src.name}",
                kwargs={"scraper_cls": scraper_cls, "source_name": src.name},
                next_run_time=None,  # 不立即执行，等服务启动完再说
                misfire_grace_time=300,
            )
            logger.info(f"注册定时任务: {src.name} 每 {interval_minutes} 分钟")

    def start(self):
        self.scheduler.start()
        logger.info("采集调度器已启动")

    def shutdown(self):
        self.scheduler.shutdown(wait=True)
        logger.info("采集调度器已关闭")

    async def run_now(self, source_id: int) -> dict:
        """立即执行指定数据源的采集"""
        if source_id not in SCRAPER_REGISTRY:
            return {"error": f"数据源 {source_id} 没有对应的爬虫实现"}

        scraper_cls = SCRAPER_REGISTRY[source_id]
        async with self.db_factory() as db:
            src = await db.get(DataSource, source_id)
            name = src.name if src else f"source_{source_id}"

        return await self._run_scraper(scraper_cls, name)

    async def _run_scraper(self, scraper_cls: type, source_name: str):
        """执行单个爬虫的采集"""
        logger.info(f"开始采集: {source_name}")
        scraper = scraper_cls()
        try:
            stats = await self._pipeline.run(scraper)
            logger.info(
                f"采集完成: {source_name} | "
                f"抓取={stats['items_scraped']} "
                f"新增={stats['items_new']} "
                f"更新={stats['items_updated']} "
                f"跳过={stats['items_skipped']}"
            )
            return stats
        except Exception as e:
            logger.error(f"采集异常: {source_name}: {e}", exc_info=True)
            return {"error": str(e)}
