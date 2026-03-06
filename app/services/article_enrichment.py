from datetime import datetime, timezone
from app.services.article_scraper import scrape_article_text
from app.services.cache import get_cached_article, set_cached_article

def enrich_articles_with_text(articles: list[dict], max_articles: int = 25) -> list[dict]:
    out = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for a in articles[:max_articles]:
        url = a.get("link", "")
        if not url:
            continue

        cached = get_cached_article(url)
        if cached is not None:
            aa = dict(a)
            aa["content"] = cached
            aa["content_source"] = "cache"
            out.append(aa)
            continue

        text = scrape_article_text(url)
        if text:
            set_cached_article(url, text, now_iso)

        aa = dict(a)
        aa["content"] = text
        aa["content_source"] = "scrape" if text else "empty"
        out.append(aa)

    return out