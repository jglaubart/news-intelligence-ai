import re
import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

def _clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s

def scrape_article_text(url: str, timeout: int = 12, max_chars: int = 12000) -> str:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()

        ps = soup.find_all("p")
        text = " ".join(_clean_text(p.get_text(" ", strip=True)) for p in ps)
        text = _clean_text(text)

        if len(text) > max_chars:
            text = text[:max_chars]
        return text
    except Exception:
        return ""