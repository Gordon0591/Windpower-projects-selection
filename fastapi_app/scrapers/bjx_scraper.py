from __future__ import annotations
"""北极星风力发电网爬虫 — https://fd.bjx.com.cn/"""

import re
from datetime import datetime
from typing import AsyncIterator
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScrapedArticle


class BjxScraper(BaseScraper):
    """
    北极星风力发电网爬虫

    目标频道:
      - 风电产业  https://fd.bjx.com.cn/fdcy/
      - 风电项目  https://fd.bjx.com.cn/fdxm/
      - 海上风电  https://fd.bjx.com.cn/hsfd/
    """

    source_id: int = 1
    source_name: str = "北极星风力发电网"
    base_url: str = "https://fd.bjx.com.cn/"

    # 采集频道及其翻页范围（覆盖 2025年7月 ~ 2026年5月）
    # 分页格式: /xm/1/, /xm/2/ — 每页 64 篇文章
    CHANNELS = [
        {"path": "/xm/",   "name": "风电项目", "page_start": 1,  "page_end": 26},   # p3=2026-05, p25=2025-07
        {"path": "/fdcy/", "name": "风电产业", "page_start": 1,  "page_end": 26},   # p3=2026-05, p25=2025-07
        {"path": "/hsfd/", "name": "海上风电", "page_start": 1,  "page_end": 16},   # p4=2026-04, p15=2025-06
    ]

    # 文章 URL 正则（过滤掉导航链接、专题页等）
    ARTICLE_URL_PATTERN = re.compile(
        r"https?://news\.bjx\.com\.cn/html/\d{8}/\d+\.shtml"
    )

    async def list_page_urls(self) -> list[str]:
        """生成各频道列表页 URL — 使用 /{channel}/{page}/ 格式"""
        urls = []
        for ch in self.CHANNELS:
            base = urljoin(self.base_url, ch["path"])
            for page in range(ch["page_start"], ch["page_end"] + 1):
                if page == 1:
                    urls.append(base)  # 第 1 页不带数字
                else:
                    urls.append(f"{base}{page}/")
        return urls

    async def parse_list_page(
        self, soup: BeautifulSoup, list_url: str
    ) -> AsyncIterator[dict]:
        """
        解析北极星列表页

        文章链接格式: https://news.bjx.com.cn/html/YYYYMMDD/xxxxxxx.shtml
        标题通常在 <a> 标签的 title 属性或文本中
        """
        # 找所有 <a> 标签
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            url = urljoin(self.base_url, href)

            # 只处理文章链接（过滤导航、专题页等）
            if not self.ARTICLE_URL_PATTERN.match(url):
                continue

            # 提取标题（优先 title 属性，其次文本）
            title = a_tag.get("title", "").strip() or a_tag.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            # 提取日期（从父节点找）
            date_tag = a_tag.find_parent(["li", "div"]).find(
                "span", class_=re.compile(r"time|date", re.I)
            ) if a_tag.find_parent(["li", "div"]) else None
            publish_date = None
            if date_tag:
                publish_date = self._parse_date(date_tag.get_text(strip=True))

            # 关键词过滤
            if self._is_relevant(title):
                yield {"url": url, "title": title, "date": publish_date}

    # ── 辅助方法 ─────────────────────────────────────────

    @staticmethod
    def _is_relevant(title: str) -> bool:
        """判断标题是否与风电项目相关"""
        keywords = [
            "风电", "风电场", "风机", "风电机组", "风电项目",
            "核准", "批复", "招标", "中标", "开工", "并网", "吊装", "完工",
            "海上风电", "陆上风电", "分散式", "大基地",
            "金风", "远景", "明阳", "运达", "三一重能", "东方风电",
            "中国海装", "中车", "电气风电", "华能", "华电", "国家能源",
            "大唐", "国家电投", "中广核", "三峡",
            "塔筒", "混塔", "钢塔", "齿轮箱", "叶片", "变流器",
            "大MW", "MW级", "GW",
            "新能源", "可再生能源",
        ]
        return any(kw in title for kw in keywords)

    @staticmethod
    def _parse_date(text: str) -> datetime | None:
        """解析日期字符串"""
        patterns = [
            r"(\d{4})-(\d{1,2})-(\d{1,2})",
            r"(\d{4})/(\d{1,2})/(\d{1,2})",
            r"(\d{4})\.(\d{1,2})\.(\d{1,2})",
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                try:
                    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                except ValueError:
                    pass
        return None
