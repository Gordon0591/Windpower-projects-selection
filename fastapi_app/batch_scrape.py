#!/usr/bin/env python3
"""批量采集脚本 — 抓取 2025年7月 ~ 2026年5月 风电项目数据

用法:
  python batch_scrape.py                # 运行采集
  python batch_scrape.py --dry-run      # 仅列出要抓取的页面数
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from scrapers.bjx_scraper import BjxScraper
from scrapers.llm_extractor import LLMExtractor
from scrapers.pipeline import ScrapePipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("batch_scrape")


async def main():
    # SQLite 异步引擎
    db_path = os.path.join(os.path.dirname(__file__), "wind_power.db")
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
    db_factory = async_sessionmaker(engine, expire_on_commit=False)

    # 初始化
    extractor = LLMExtractor()
    pipeline = ScrapePipeline(db_factory, extractor)
    scraper = BjxScraper()

    # 统计要抓取的页面
    list_urls = await scraper.list_page_urls()
    logger.info(f"{'='*60}")
    logger.info(f"数据源: {scraper.source_name}")
    logger.info(f"频道数: {len(scraper.CHANNELS)}")
    logger.info(f"列表页数: {len(list_urls)}")
    logger.info(f"预估文章数: ~{len(list_urls) * 64} (每页约64篇)")
    logger.info(f"目标时段: 2025年7月 ~ 2026年5月")
    logger.info(f"{'='*60}")

    if "--dry-run" in sys.argv:
        logger.info("Dry-run 模式，不执行采集。")
        return

    # 确认
    print(f"\n将抓取 {len(list_urls)} 个列表页，预估 ~{len(list_urls)*64} 篇文章")
    print("Claude Haiku 将提取项目信息（仅处理风电相关的文章）")
    ans = input("继续？[y/N] ")
    if ans.lower() not in ("y", "yes"):
        print("已取消")
        return

    # 执行采集
    start = datetime.now()
    logger.info("开始采集...")
    try:
        stats = await pipeline.run(scraper)
    finally:
        await engine.dispose()

    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"{'='*60}")
    logger.info(f"采集完成！耗时 {elapsed/60:.1f} 分钟")
    logger.info(f"  抓取文章: {stats.get('items_scraped', 0)}")
    logger.info(f"  新增项目: {stats.get('items_new', 0)}")
    logger.info(f"  更新项目: {stats.get('items_updated', 0)}")
    logger.info(f"  跳过:     {stats.get('items_skipped', 0)}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
