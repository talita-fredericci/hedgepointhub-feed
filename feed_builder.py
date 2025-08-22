#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIY RSS for Hedgepoint HUB blog (index-based)
--------------------------------------------
- Queries Bing for "site:hedgepointhub.com.br/blog"
- Picks the newest result (by datePublished/dateLastCrawled when available)
- Generates feed.xml (RSS 2.0) with that single most-recent item
- If BING_API_KEY is provided, uses Bing Web Search API (more reliable).
  Else, falls back to scraping Bing HTML (works, but dates may be missing).
"""

import os
import sys
import time
import email.utils
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import requests
from bs4 import BeautifulSoup

QUERY = "site:hedgepointhub.com.br/blog"
SITE_TITLE = "Hedgepoint HUB – Novos Relatórios (via índice)"
SITE_LINK = "https://www.hedgepointhub.com.br/blog/"
SITE_DESC = "Feed não-oficial gerado a partir de resultados indexados em buscadores."
OUTPUT_FILE = "feed.xml"


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip()


def search_bing_api(query: str) -> Optional[Dict[str, Any]]:
    api_key = get_env("BING_API_KEY")
    if not api_key:
        return None

    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "q": query,
        "mkt": "pt-BR",
        "count": 10,
        "responseFilter": "Webpages",
        "freshness": "Week",
        "textDecorations": False,
        "textFormat": "Raw",
    }
    try:
        r = requests.get(endpoint, headers=headers, params=params, timeout=25)
        r.raise_for_status()
        data = r.json()
        items = data.get("webPages", {}).get("value", [])
        if not items:
            return None

        best = None
        best_date = None
        for it in items:
            title = it.get("name")
            url = it.get("url")
            snippet = it.get("snippet")
            date_str = it.get("datePublished") or it.get("dateLastCrawled")
            dt = None
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception:
                    dt = None

            if best is None or (dt and (best_date is None or dt >= best_date)):
                best = {"title": title, "url": url, "snippet": snippet, "date": dt}
                best_date = dt

        return best
    except Exception as e:
        print(f"[WARN] Bing API failed: {e}", file=sys.stderr)
        return None


def search_bing_html(query: str) -> Optional[Dict[str, Any]]:
    url = "https://www.bing.com/search"
    params = {"q": query, "setlang": "pt-BR", "cc": "br"}
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        results = soup.select("li.b_algo")
        if not results:
            return None

        first = results[0]
        a = first.select_one("h2 a")
        title = a.get_text(strip=True) if a else None
        href = a["href"] if (a and a.has_attr("href")) else None
        snippet_el = first.select_one(".b_caption p")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        if not (title and href):
            return None

        return {"title": title, "url": href, "snippet": snippet, "date": None}
    except Exception as e:
        print(f"[WARN] Bing HTML scrape failed: {e}", file=sys.stderr)
        return None


def clean_url(u: str) -> str:
    return u.split("?")[0] if "?" in u else u


def rfc2822(dt: datetime) -> str:
    # Generate RFC2822 timestamp for RSS pubDate/lastBuildDate
    return email.utils.format_datetime(dt.astimezone(timezone.utc))


def build_rss(item: Optional[Dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc)
    last_build = rfc2822(now)

    if not item:
        # Empty feed but still valid
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{SITE_TITLE}</title>
    <link>{SITE_LINK}</link>
    <description>{SITE_DESC}</description>
    <lastBuildDate>{last_build}</lastBuildDate>
    <generator>Custom GitHub Actions</generator>
  </channel>
</rss>
""".strip()
        return xml

    title = (item.get("title") or "").strip()
    url = clean_url(item.get("url") or "")
    desc = (item.get("snippet") or "").strip()

    dt = item.get("date")
    pub_date = rfc2822(dt) if isinstance(dt, datetime) else last_build
    guid = url or (title + pub_date)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{SITE_TITLE}</title>
    <link>{SITE_LINK}</link>
    <description>{SITE_DESC}</description>
    <lastBuildDate>{last_build}</lastBuildDate>
    <generator>Custom GitHub Actions</generator>

    <item>
      <title>{escape_xml(title)}</title>
      <link>{escape_xml(url)}</link>
      <guid isPermaLink="true">{escape_xml(guid)}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{escape_xml(desc)}</description>
    </item>
  </channel>
</rss>
""".strip()
    return xml


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&apos;")
    )


def main() -> int:
    item = search_bing_api(QUERY)
    if not item:
        item = search_bing_html(QUERY)

    # Sanity: ensure it's a HUB blog URL
    if item and "hedgepointhub.com.br/blog" not in (item.get("url") or ""):
        item = None

    xml = build_rss(item)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"[OK] Wrote {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
