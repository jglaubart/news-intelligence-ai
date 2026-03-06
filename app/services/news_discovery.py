from __future__ import annotations

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import List, Dict
import urllib.parse
import requests
import feedparser
from bs4 import BeautifulSoup


def _parse_pubdate(s: str):
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _filter_by_days_back(articles: List[Dict], days_back: int) -> List[Dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    out = []
    for a in articles:
        dt = _parse_pubdate(a.get("published", ""))
        if dt is None:
            out.append(a)
        elif dt >= cutoff:
            out.append(a)
    return out


def _google_news_rss_url(query: str, lang: str = "es-419", country: str = "AR") -> str:
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={country}&ceid={country}:{lang}"


def _is_google_news_url(url: str) -> bool:
    if not url:
        return False
    return "news.google.com" in url


def _extract_real_url_from_html(html: str) -> str | None:
    """
    En muchos RSS de Google News, el summary trae HTML con anchors.
    Acá buscamos el primer href que NO sea de news.google.com.
    """
    if not html:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href and not _is_google_news_url(href):
                return href
    except Exception:
        return None

    return None


def _extract_real_url(entry) -> str | None:
    """
    Intenta sacar la URL real del medio desde varios lugares del entry.
    """

    # 1) summary / summary_detail
    real = _extract_real_url_from_html(entry.get("summary", ""))
    if real:
        return real

    summary_detail = entry.get("summary_detail", {})
    if isinstance(summary_detail, dict):
        real = _extract_real_url_from_html(summary_detail.get("value", ""))
        if real:
            return real

    # 2) links del entry
    for link_obj in entry.get("links", []):
        href = link_obj.get("href", "").strip()
        if href and not _is_google_news_url(href):
            return href

    # 3) source.href
    source = entry.get("source")
    if source:
        href = getattr(source, "href", "") or ""
        if href and not _is_google_news_url(href):
            return href

    return None


def discover_news(
    queries: List[str],
    max_per_query: int = 15,
    days_back: int = 30,
    timeout_sec: int = 12
) -> List[Dict]:
    """
    Devuelve lista de artículos con:
    - title
    - link (preferentemente real del medio)
    - google_link (link original de Google News)
    - published
    - source
    """
    all_articles: List[Dict] = []

    for q in queries:
        url = _google_news_rss_url(q)

        resp = requests.get(
            url,
            timeout=timeout_sec,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.raise_for_status()

        feed = feedparser.parse(resp.content)

        for entry in feed.entries[:max_per_query]:
            source = ""
            try:
                source = getattr(getattr(entry, "source", None), "title", "") or ""
            except Exception:
                source = ""

            google_link = entry.get("link", "")
            real_link = _extract_real_url(entry) or google_link

            all_articles.append({
                "title": entry.get("title", ""),
                "link": real_link,
                "google_link": google_link,
                "published": entry.get("published", "") or entry.get("updated", ""),
                "source": source,
            })

    all_articles = _filter_by_days_back(all_articles, days_back)
    return all_articles