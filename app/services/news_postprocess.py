from urllib.parse import urlparse


def _norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def dedupe_articles(articles: list[dict]) -> list[dict]:
    seen = set()
    out = []

    for a in articles:
        key = (_norm(a.get("title", "")), _norm(a.get("source", "")))
        if key in seen:
            continue
        seen.add(key)
        out.append(a)

    return out


def score_article(article: dict, topic: str, keywords_primary: list[str]) -> int:
    title = _norm(article.get("title", ""))
    source = _norm(article.get("source", ""))
    text = f"{title} {source}"

    score = 0

    topic_words = [w for w in _norm(topic).split() if len(w) > 3]
    for word in topic_words:
        if word in text:
            score += 3

    for kw in keywords_primary or []:
        kw_words = [w for w in _norm(kw).split() if len(w) > 3]
        matches = sum(1 for w in kw_words if w in text)
        score += matches

    if any(word in title for word in ["inflacion", "ipc", "indec", "precios"]):
        score += 4

    if any(x in source for x in ["infobae", "ambito", "cronista", "lanacion", "clarin", "perfil", "bloomberg"]):
        score += 1

    return score


def rank_and_limit(articles: list[dict], topic: str, keywords_primary: list[str], limit: int = 40) -> list[dict]:
    scored = []

    for a in articles:
        score = score_article(a, topic, keywords_primary)
        aa = dict(a)
        aa["score"] = score
        scored.append(aa)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]