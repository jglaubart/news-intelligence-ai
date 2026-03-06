import re
import sqlite3
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


DB_PATH = "news_cache.db"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

MAX_CONTENT_CHARS = 12000
MIN_CONTENT_CHARS = 180


def _init_cache():
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


_init_cache()


def _get_cached(url: str):
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


def _save_cache(url: str, final_url: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO article_cache(url, final_url, content, created_at) VALUES (?, ?, ?, ?)",
        (url, final_url, content, datetime.utcnow().isoformat()),
    )

    conn.commit()
    conn.close()


def _clean_text(text: str) -> str:
    text = text or ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _looks_like_homepage(url: str) -> bool:
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        return path == ""
    except Exception:
        return False


def _remove_noise_nodes(soup: BeautifulSoup):
    for tag in soup([
        "script", "style", "noscript", "svg", "form",
        "header", "footer", "nav", "aside"
    ]):
        tag.decompose()

    # Sacar bloques muy comunes de ruido
    noise_selectors = [
        '[class*="header"]',
        '[class*="footer"]',
        '[class*="sidebar"]',
        '[class*="menu"]',
        '[class*="nav"]',
        '[class*="related"]',
        '[class*="recommend"]',
        '[class*="newsletter"]',
        '[class*="ads"]',
        '[class*="banner"]',
        '[class*="share"]',
        '[class*="social"]',
        '[id*="header"]',
        '[id*="footer"]',
        '[id*="sidebar"]',
        '[id*="menu"]',
        '[id*="nav"]',
    ]

    for selector in noise_selectors:
        for node in soup.select(selector):
            node.decompose()


def _extract_from_candidate_nodes(nodes) -> str:
    paragraphs = []

    for node in nodes:
        for p in node.find_all("p"):
            txt = _clean_text(p.get_text(" ", strip=True))
            if len(txt) >= 40:
                paragraphs.append(txt)

    return _clean_text(" ".join(paragraphs))


def _extract_article_text_from_soup(soup: BeautifulSoup) -> str:
    # Primero, selectores típicos de contenido principal
    candidate_selectors = [
        "article",
        "main article",
        '[itemprop="articleBody"]',
        '[class*="article-body"]',
        '[class*="articleBody"]',
        '[class*="story-body"]',
        '[class*="storyBody"]',
        '[class*="post-content"]',
        '[class*="postContent"]',
        '[class*="entry-content"]',
        '[class*="entryContent"]',
        '[class*="content-body"]',
        '[class*="contentBody"]',
        '[class*="news-body"]',
        '[class*="newsBody"]',
        '[class*="nota-body"]',
        '[class*="article-content"]',
        '[class*="articleContent"]',
        '[id*="article-body"]',
        '[id*="articleBody"]',
        '[id*="content-body"]',
        '[id*="contentBody"]',
        "main",
    ]

    for selector in candidate_selectors:
        nodes = soup.select(selector)
        if not nodes:
            continue

        text = _extract_from_candidate_nodes(nodes)
        if len(text) >= MIN_CONTENT_CHARS:
            return text

    # Fallback: todos los párrafos
    paragraphs = []
    for p in soup.find_all("p"):
        txt = _clean_text(p.get_text(" ", strip=True))
        if len(txt) >= 40:
            paragraphs.append(txt)

    return _clean_text(" ".join(paragraphs))


def _is_bad_content(text: str) -> bool:
    if not text:
        return True

    low = text.lower()

    # Muy corto
    if len(text) < MIN_CONTENT_CHARS:
        return True

    # Casos típicos de basura
    bad_patterns = [
        "loading widget",
        "suscribite",
        "iniciá sesión",
        "términos y condiciones",
        "todos los derechos reservados",
        "seguinos en",
        "más noticias más noticias",
    ]

    if any(pat in low for pat in bad_patterns):
        return True

    # Mucha repetición típica de home/portada
    if low.count("dólar oficial") >= 2:
        return True

    if low.count("por ") > 20:
        return True

    return False


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
        if _looks_like_homepage(final_url):
            return ""

        r = requests.get(final_url, headers=HEADERS, timeout=12, allow_redirects=True)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "lxml")
        _remove_noise_nodes(soup)

        text = _extract_article_text_from_soup(soup)
        text = _clean_text(text)

        if _is_bad_content(text):
            return ""

        if len(text) > MAX_CONTENT_CHARS:
            text = text[:MAX_CONTENT_CHARS]

        return text

    except Exception:
        return ""


def enrich_articles_with_text(articles: list, max_articles: int = 25):
    enriched = []

    for article in articles[:max_articles]:
        url = article.get("link")
        google_link = article.get("google_link")

        if not url and not google_link:
            continue

        cache_key = url or google_link

        cached = _get_cached(cache_key)
        if cached:
            article_copy = dict(article)
            article_copy["final_url"] = cached["final_url"]
            article_copy["content"] = cached["content"]
            article_copy["content_source"] = "cache"
            enriched.append(article_copy)
            continue

        final_url = resolve_final_url(url or google_link)

        text = scrape_article(final_url)

        # si link era una home, intentá al menos con el google_link
        if not text and google_link and google_link != url:
            alt_final_url = resolve_final_url(google_link)
            alt_text = scrape_article(alt_final_url)

            if len(alt_text) > len(text):
                final_url = alt_final_url
                text = alt_text

        _save_cache(cache_key, final_url, text)

        article_copy = dict(article)
        article_copy["final_url"] = final_url
        article_copy["content"] = text
        article_copy["content_source"] = "scrape"

        enriched.append(article_copy)

    return enriched