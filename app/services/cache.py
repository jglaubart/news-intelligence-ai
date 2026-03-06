import sqlite3
from typing import Optional

DB_PATH = "cache.sqlite3"

def init_cache():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS articles_cache (
            url TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    con.commit()
    con.close()

def get_cached_article(url: str) -> Optional[str]:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT content FROM articles_cache WHERE url = ?", (url,))
    row = cur.fetchone()
    con.close()
    return row[0] if row else None

def set_cached_article(url: str, content: str, created_at_iso: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO articles_cache(url, content, created_at) VALUES (?, ?, ?)",
        (url, content, created_at_iso),
    )
    con.commit()
    con.close()