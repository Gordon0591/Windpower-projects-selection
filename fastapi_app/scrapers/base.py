from __future__ import annotations
"""爬虫基类 — 提供 HTTP 请求、重试、HTML 清洗等公共能力"""

import hashlib
import logging
import random
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapedArticle:
    """爬取到的原始文章"""
    url: str
    title: str
    content: str                 # 清洗后的纯文本
    raw_html: str
    publish_date: datetime | None = None
    source_name: str = ""        # 数据源名称，如 "北极星风力发电网"


class BaseScraper(ABC):
    """
    爬虫基类
    子类只需实现:
      - list_page_urls():  返回要抓取的列表页 URL
      - parse_list_page():  解析列表页，yield 文章 URL + 标题 + 日期
    """

    # 子类覆盖
    source_id: int = 0
    source_name: str = ""
    base_url: str = ""

    # HTTP 配置
    request_delay: tuple[float, float] = (1.0, 3.0)   # 请求间隔范围(秒)
    timeout: float = 30.0
    max_retries: int = 3
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    # 默认浏览器 headers（防止 Cloudflare WAF）
    default_headers: dict = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
    }

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client
        self._own_client = False
        # 已抓取的 URL 集合（内存去重，单次运行）
        self._seen_urls: set[str] = set()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "User-Agent": self.user_agent,
                **self.default_headers,
            }
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers,
                follow_redirects=True,
            )
            self._own_client = True
        return self._client

    async def close(self):
        if self._own_client and self._client:
            await self._client.aclose()

    # ── HTTP 工具 ────────────────────────────────────────

    async def _fetch(self, url: str, retries: int | None = None, referer: str = "") -> httpx.Response | None:
        """带重试的 HTTP GET"""
        retries = retries if retries is not None else self.max_retries
        client = await self._get_client()

        headers = {}
        if referer:
            headers["Referer"] = referer
        # 如果是跨域文章详情页，加 Sec-Fetch 头模拟真实浏览器行为
        if "news.bjx.com.cn" in url:
            headers["Sec-Fetch-Dest"] = "document"
            headers["Sec-Fetch-Mode"] = "navigate"
            headers["Sec-Fetch-Site"] = "same-site"

        for attempt in range(retries):
            try:
                resp = await client.get(url, headers=headers if headers else None)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503):
                    wait = 2 ** attempt * 5
                    logger.warning(f"Rate limited on {url}, waiting {wait}s")
                    await self._sleep(wait)
                    continue
                elif e.response.status_code == 404:
                    logger.info(f"404: {url}")
                    return None
                else:
                    logger.error(f"HTTP {e.response.status_code} on {url}")
                    if attempt == retries - 1:
                        return None
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                logger.warning(f"Network error on {url}: {e}, retry {attempt+1}/{retries}")
                await self._sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None
        return None

    async def _sleep(self, seconds: float):
        await __import__("asyncio").sleep(seconds)

    # ── HTML 解析工具 ────────────────────────────────────

    @staticmethod
    def parse_html(html: str, base_url: str = "") -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @staticmethod
    def clean_html(soup: BeautifulSoup) -> str:
        """从 HTML 提取纯净正文文本"""
        # 移除无用标签
        for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                                   "aside", "iframe", "noscript", "form"]):
            tag.decompose()

        # 尝试找到正文容器
        article = (
            soup.find("article") or
            soup.find("div", class_=re.compile(r"article|content|body|text|main|news",
                                                 re.I)) or
            soup
        )

        # 提取文本
        text = article.get_text(separator="\n", strip=True)

        # 压缩空白行
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)

        return text.strip()

    @staticmethod
    def content_hash(content: str) -> str:
        """内容 MD5，用于去重"""
        # 取前 2000 字符做 hash，提高效率
        return hashlib.md5(content[:2000].encode()).hexdigest()

    # ── 抽象方法 ─────────────────────────────────────────

    @abstractmethod
    async def list_page_urls(self) -> list[str]:
        """返回要抓取的列表页 URL 列表"""
        ...

    @abstractmethod
    async def parse_list_page(self, soup: BeautifulSoup, list_url: str) -> AsyncIterator[dict]:
        """
        解析列表页，yield 文章信息:
          {"url": str, "title": str, "date": datetime | None}
        """
        ...

    # ── 主流程 ───────────────────────────────────────────

    async def scrape(self) -> AsyncIterator[ScrapedArticle]:
        """主采集流程：遍历列表页 → 抓取文章 → 清洗 → yield"""
        list_urls = await self.list_page_urls()

        for list_url in list_urls:
            # 请求间隔
            delay = random.uniform(*self.request_delay)
            await self._sleep(delay)

            resp = await self._fetch(list_url)
            if not resp:
                continue

            soup = self.parse_html(resp.text, list_url)
            async for article_meta in self.parse_list_page(soup, list_url):
                url = article_meta["url"]

                # URL 去重
                if url in self._seen_urls:
                    continue
                self._seen_urls.add(url)

                # 请求间隔
                await self._sleep(random.uniform(*self.request_delay))

                # 抓取文章详情
                article_resp = await self._fetch(url)
                if not article_resp:
                    continue

                article_soup = self.parse_html(article_resp.text, url)
                content = self.clean_html(article_soup)

                # 太短的内容跳过
                if len(content) < 100:
                    logger.info(f"Content too short ({len(content)} chars): {url}")
                    continue

                yield ScrapedArticle(
                    url=url,
                    title=article_meta.get("title", ""),
                    content=content,
                    raw_html=article_resp.text,
                    publish_date=article_meta.get("date"),
                    source_name=self.source_name,
                )
