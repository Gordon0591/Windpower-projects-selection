#!/usr/bin/env python3
"""
爬虫核心链路验证脚本 v2
修复: 浏览器级 headers + 文章链接正则过滤 + 正文提取
"""

import html
import re
import ssl
import time
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

# ── 模拟浏览器 ──────────────────────────────────────────
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}

BASE_URL = "https://fd.bjx.com.cn"
CHANNELS = [
    {"path": "/fdcy/", "name": "风电产业", "max_pages": 1},
    {"path": "/xm/",   "name": "风电项目", "max_pages": 1},   # 修正: /xm/ 不是 /fdxm/
    {"path": "/hsfd/", "name": "海上风电", "max_pages": 1},
]
REQUEST_DELAY = 2.0
MAX_DETAIL_FETCH = 2  # 最多抓几篇详情验证

# ── 文章链接正则 ────────────────────────────────────────
ARTICLE_URL_PATTERN = re.compile(
    r"https?://news\.bjx\.com\.cn/html/\d{8}/\d+\.shtml"
)

# ── 风电关键词 ──────────────────────────────────────────
PROJECT_KW = [
    "风电", "风电场", "风机", "风电机组", "风电项目",
    "核准", "批复", "招标", "中标", "开工", "并网", "吊装", "完工",
    "海上风电", "陆上风电", "分散式", "大基地",
    "金风", "远景", "明阳", "运达", "三一重能", "东方风电",
    "中国海装", "中车", "电气风电",
    "华能", "华电", "国家能源", "大唐", "国家电投", "中广核", "三峡",
    "塔筒", "混塔", "钢塔",
]


# ── HTTP ────────────────────────────────────────────────

def fetch(url, referer="", timeout=30, cross_domain=False):
    """HTTP GET — 跨域文章详情页使用增强 headers 防 WAF"""
    headers = {"User-Agent": BROWSER_HEADERS["User-Agent"]}
    if cross_domain or "news.bjx.com.cn" in url:
        headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-site",
        })
    if referer:
        headers["Referer"] = referer

    req = urllib.request.Request(url, headers=headers)
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode("utf-8", errors="replace"), resp.geturl()
    except Exception as e:
        print(f"  ❌ {e}")
        return None, None


# ── HTML 解析 ───────────────────────────────────────────

class LinkExtractor(HTMLParser):
    """提取所有链接"""
    def __init__(self):
        super().__init__()
        self.links = []  # [(href, text)]
        self._current_href = ""
        self._current_text = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        href = attrs.get("href", "")
        if tag == "a" and href:
            self._current_href = href
            self._current_text = ""
        else:
            self._current_href = ""

    def handle_data(self, data):
        if self._current_href:
            self._current_text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._current_href:
            self.links.append((self._current_href, self._current_text.strip()))
            self._current_href = ""


def clean_html(html_text):
    """清洗 HTML → 纯文本"""
    # 移除 script/style/nav/footer/header
    for tag in ["script", "style", "nav", "footer", "header", "aside", "iframe"]:
        html_text = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html_text, flags=re.DOTALL | re.I)
    # 移除标签
    text = re.sub(r"<[^>]+>", "\n", html_text)
    # 解码实体
    text = html.unescape(text)
    # 压缩空白
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_article_info(html_text, url):
    """从文章页提取标题和正文"""
    # 尝试多种标题提取方式
    title = ""
    for pat in [
        r'<title[^>]*>(.*?)</title>',
        r'class="article[^"]*title[^"]*"[^>]*>(.*?)<',
        r'class="news[^"]*title[^"]*"[^>]*>(.*?)<',
        r'<h1[^>]*>(.*?)</h1>',
        r'<h2[^>]*>(.*?)</h2>',
    ]:
        m = re.search(pat, html_text, re.I | re.DOTALL)
        if m:
            title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if len(title) > 5:
                break

    # 正文提取：找 article/content 容器
    body = ""
    for pat in [
        r'class="article[^"]*body[^"]*"[^>]*>(.*?)</div>',
        r'class="article[^"]*content[^"]*"[^>]*>(.*?)</div>',
        r'class="news[^"]*content[^"]*"[^>]*>(.*?)</div>',
        r'<article[^>]*>(.*?)</article>',
    ]:
        m = re.search(pat, html_text, re.I | re.DOTALL)
        if m:
            body = clean_html(m.group(1))
            if len(body) > 200:
                break

    # fallback: 直接用 clean_html
    if not body:
        body = clean_html(html_text)

    return title, body


def is_relevant(title):
    return any(kw in title for kw in PROJECT_KW)


# ── 主流程 ──────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  风电爬虫核心链路验证 v2")
    print(f"  目标: {BASE_URL}")
    print("=" * 65)

    total_articles = 0
    total_relevant = 0
    detail_samples = []

    for ch in CHANNELS:
        list_url = urljoin(BASE_URL, ch["path"])
        print(f"\n── {ch['name']}: {list_url} ──")

        time.sleep(REQUEST_DELAY)

        # Step 1: 列表页
        html, final_url = fetch(list_url)
        if not html:
            print(f"  ❌ 列表页获取失败")
            continue
        print(f"  ✅ 获取成功 ({len(html):,} bytes)")

        # Step 2: 提取所有链接
        parser = LinkExtractor()
        parser.feed(html)

        # 只在文章链接中找
        all_links = parser.links
        article_links = [
            (href, text) for href, text in all_links
            if ARTICLE_URL_PATTERN.match(urljoin(BASE_URL, href))
        ]
        print(f"  📄 文章链接: {len(article_links)} 篇")

        # Step 3: 关键词过滤
        relevant = [(h, t) for h, t in article_links if is_relevant(t)]
        print(f"  🎯 风电相关: {len(relevant)} 篇")

        if relevant:
            # 打印前 5 篇标题
            for i, (href, title) in enumerate(relevant[:5]):
                print(f"     [{i+1}] {title[:60]}")

        total_articles += len(article_links)
        total_relevant += len(relevant)

        # Step 4: 抓取详情
        for href, title in relevant[:MAX_DETAIL_FETCH]:
            art_url = urljoin(BASE_URL, href)
            print(f"\n  ── 详情: {title[:55]}...")
            print(f"     URL: {art_url}")

            time.sleep(REQUEST_DELAY)
            art_html, _ = fetch(art_url, referer=list_url, cross_domain=True)
            if not art_html:
                continue

            # 检查 Cloudflare WAF
            if "CF_APP_WAF" in art_html[:1000] or ("验证" in art_html[:300] and len(art_html) < 2000):
                print(f"     ⚠️  Cloudflare 验证页面")
                continue

            extracted_title, body = extract_article_info(art_html, art_url)
            print(f"     标题: {extracted_title or title}")
            print(f"     正文: {len(body)} 字符")
            print(f"     预览: {body[:150].replace(chr(10), ' ')}...")

            detail_samples.append({
                "title": extracted_title or title,
                "url": art_url,
                "length": len(body),
                "preview": body[:500],
            })
            break  # 每频道只取 1 篇

    # ── 汇总 ──────────────────────────────────────────
    print(f"\n{'=' * 65}")
    print(f"  汇总")
    print(f"  文章链接总数:   {total_articles}")
    print(f"  风电相关:       {total_relevant}")
    print(f"  成功抓取详情:   {len(detail_samples)} 篇")
    print(f"{'=' * 65}")

    if detail_samples:
        s = detail_samples[0]
        print(f"\n📤 LLM 提取样本:")
        print(f"  标题: {s['title']}")
        print(f"  URL: {s['url']}")
        print(f"  正文({s['length']}字):\n{s['preview'][:400]}...")
        print(f"\n✅ Pipeline 验证通过: 列表页→文章链接→详情→清洗 全链路正常")
    elif total_relevant > 0:
        print(f"\n⚠️  列表页正常，但详情页被拦截（Cloudflare）——生产环境需用 Playwright")
    else:
        print(f"\n⚠️  未找到风电相关文章链接——可能需要更新关键词或页面结构")


if __name__ == "__main__":
    main()
