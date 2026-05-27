# -*- coding: utf-8 -*-
"""网络热词抓取模块 — 带重试和超时保护"""

import logging

logger = logging.getLogger(__name__)

try:
    import requests
    from bs4 import BeautifulSoup
    _HAS_SCRAPING = True
except ImportError:
    _HAS_SCRAPING = False

MAX_RETRIES = 2
TIMEOUT = 10


def scrape_google_trends_th() -> tuple[list[str], str]:
    if not _HAS_SCRAPING:
        return [], "缺少依赖: pip install requests beautifulsoup4"

    for attempt in range(MAX_RETRIES + 1):
        try:
            url = "https://trends.google.co.th/trending/rss?geo=TH"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "th-TH,th;q=0.9",
            }
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            if resp.status_code != 200:
                if attempt < MAX_RETRIES:
                    continue
                return [], f"Google Trends 返回状态码: {resp.status_code}"

            soup = BeautifulSoup(resp.content, "html.parser")
            keywords = []
            for item in soup.find_all("item"):
                title_tag = item.find("title")
                if title_tag and title_tag.text.strip():
                    keywords.append(title_tag.text.strip())
                if len(keywords) >= 20:
                    break

            if not keywords:
                if attempt < MAX_RETRIES:
                    continue
                return [], "未获取到热词（可能地区限制或网络问题）"

            return keywords, f"成功抓取 {len(keywords)} 条热词"

        except requests.Timeout:
            if attempt < MAX_RETRIES:
                continue
            return [], f"请求超时（{TIMEOUT}秒），请检查网络"
        except requests.ConnectionError:
            if attempt < MAX_RETRIES:
                continue
            return [], "网络连接失败，请检查网络"
        except Exception as e:
            logger.error("热词抓取异常: %s", e)
            if attempt < MAX_RETRIES:
                continue
            return [], f"抓取异常: {e}"

    return [], "抓取失败（已重试）"
