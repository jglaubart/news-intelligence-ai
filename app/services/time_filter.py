from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime


def filter_by_days(articles: list[dict], days_back: int):
    cutoff = datetime.utcnow() - timedelta(days=days_back)

    out = []

    for a in articles:
        published = a.get("published")

        try:
            dt = parsedate_to_datetime(published)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)

            if dt >= cutoff:
                out.append(a)
        except:
            continue

    return out