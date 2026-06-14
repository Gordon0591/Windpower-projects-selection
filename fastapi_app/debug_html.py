#!/usr/bin/env python3
"""调试：查看 BJX 列表页的真实 HTML 结构，找到文章链接模式"""
import re
import ssl
import urllib.request

BASE_URL = "https://fd.bjx.com.cn"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace"), resp.geturl()

# 抓取列表页
print("=== 抓取列表页 ===")
html, final_url = fetch(BASE_URL + "/fdcy/")
print(f"URL: {final_url}")
print(f"Size: {len(html)} bytes")

# 查找所有链接
links = re.findall(r'href="([^"]+)"', html)
print(f"\n=== 所有链接 ({len(links)} 个) ===")
for href in links[:50]:
    print(f"  {href}")

# 查找可能包含文章列表的 class/id
classes = set(re.findall(r'class="([^"]+)"', html))
ids = set(re.findall(r'id="([^"]+)"', html))
print(f"\n=== CSS Classes ({len(classes)} 个) ===")
for c in sorted(classes)[:30]:
    print(f"  .{c}")

# 查找 list/ul 结构
print(f"\n=== 查找 <ul> 附近内容 ===")
ul_pattern = re.findall(r'<ul[^>]*>.*?</ul>', html, re.DOTALL)
for i, ul in enumerate(ul_pattern[:3]):
    print(f"\n--- UL #{i+1} ---")
    print(ul[:500])
