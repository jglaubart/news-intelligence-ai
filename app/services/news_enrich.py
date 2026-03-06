import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import re

DB_PATH = "news_cache.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

MAX_CONTENT_CHARS = 12000


def _is_vercel() -> bool:
    return os.getenv("VERCEL") == "1"


def _cache_enabled() -> bool:
    # En Vercel desactivamos SQLite local
    return not _is_vercel()


def _init_cache():
    if not _cache_enabled():
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS article_cache (
            url TEXT PRIMARY KEY,
            final_url TEXT,
            content TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def _get_cached(url: str):
    if not _cache_enabled():
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("SELECT final_url, content FROM article_cache WHERE url = ?", (url,))
        row = cur.fetchone()

        conn.close()

        if row:
            return {
                "final_url": row[0],
                "content": row[1]
            }
        return None
    except Exception:
        return None


def _save_cache(url: str, final_url: str, content: str):
    if not _cache_enabled():
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "INSERT OR REPLACE INTO article_cache(url, final_url, content, created_at) VALUES (?, ?, ?, ?)",
            (url, final_url, content, datetime.utcnow().isoformat()),
        )

        conn.commit()
        conn.close()
    except Exception:
        pass


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def resolve_final_url(url: str) -> str:
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=12,
            allow_redirects=True
        )
        return response.url
    except Exception:
        return url


def scrape_article(final_url: str) -> str:
    try:
        r = requests.get(final_url, headers=HEADERS, timeout=12, allow_redirects=True)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "lxml")

        for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
        text = _clean_text(text)

        if len(text) > MAX_CONTENT_CHARS:
            text = text[:MAX_CONTENT_CHARS]

        return text

    except Exception:
        return ""


def enrich_articles_with_text(articles: list, max_articles: int = 25):
    _init_cache()

    enriched = []

    for article in articles[:max_articles]:
        url = article.get("link")

        if not url:
            continue

        cached = _get_cached(url)

        if cached:
            article_copy = dict(article)
            article_copy["final_url"] = cached["final_url"]
            article_copy["content"] = cached["content"]
            article_copy["content_source"] = "cache"
            enriched.append(article_copy)
            continue

        final_url = resolve_final_url(url)
        text = scrape_article(final_url)

        _save_cache(url, final_url, text)

        article_copy = dict(article)
        article_copy["final_url"] = final_url
        article_copy["content"] = text
        article_copy["content_source"] = "scrape"

        enriched.append(article_copy)

    return enriched