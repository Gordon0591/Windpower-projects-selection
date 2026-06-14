#!/usr/bin/env python3
"""采集器独立运行入口

用法:
  python run_scraper.py                     # 启动定时调度器（后台持续运行）
  python run_scraper.py --source 1          # 手动运行一次指定数据源
  python run_scraper.py --source 1 --once   # 同上
  python run_scraper.py --list              # 列出所有可用数据源
"""

import argparse
import asyncio
import logging
import os
import sys

# 确保项目路径在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import AsyncSessionLocal
from models import DataSource
from scrapers.llm_extractor import LLMExtractor
from scrapers.pipeline import ScrapePipeline
from scrapers.scheduler import SCRAPER_REGISTRY, ScrapeScheduler
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_scraper")


async def list_sources():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(DataSource).order_by(DataSource.id))
        sources = result.scalars().all()

    print("\n可用的数据源:")
    print(f"{'ID':<4} {'名称':<24} {'状态':<6} {'爬虫':<20}")
    print("-" * 60)
    for s in sources:
        scraper_name = SCRAPER_REGISTRY.get(s.id, "__class__").__name__ if s.id in SCRAPER_REGISTRY else "未实现"
        active = "✅" if s.is_active else "❌"
        print(f"{s.id:<4} {s.name:<24} {active:<6} {scraper_name:<20}")
    print()


async def run_once(source_id: int):
    scheduler = ScrapeScheduler(AsyncSessionLocal)
    stats = await scheduler.run_now(source_id)
    print(f"\n采集结果: {stats}")


async def run_scheduler():
    logger.info("启动采集调度器...")
    scheduler = ScrapeScheduler(AsyncSessionLocal)
    await scheduler.setup()
    scheduler.start()

    logger.info("调度器运行中，按 Ctrl+C 停止...")
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        scheduler.shutdown()


def main():
    parser = argparse.ArgumentParser(description="风电项目信息采集器")
    parser.add_argument("--source", type=int, help="指定数据源 ID（手动运行一次）")
    parser.add_argument("--once", action="store_true", help="仅运行一次")
    parser.add_argument("--list", action="store_true", help="列出所有数据源")
    args = parser.parse_args()

    if args.list:
        asyncio.run(list_sources())
    elif args.source:
        asyncio.run(run_once(args.source))
    elif args.once:
        # 运行所有已实现的爬虫各一次
        async def run_all():
            scheduler = ScrapeScheduler(AsyncSessionLocal)
            for source_id in SCRAPER_REGISTRY:
                print(f"\n{'='*60}")
                stats = await scheduler.run_now(source_id)
                print(f"数据源 {source_id}: {stats}")
        asyncio.run(run_all())
    else:
        asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
