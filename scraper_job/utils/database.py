import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

INSERT_NEWS_SQL = """
    INSERT INTO news (source, title, url, category, published_at, content)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (url) DO NOTHING
"""


def get_connection():
    database_url = os.environ["DATABASE_URL"]
    return psycopg.connect(database_url)


def save_news(news, source):
    inserted = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            for item in news:
                cur.execute(INSERT_NEWS_SQL, (
                    source,
                    item["title"],
                    item["url"],
                    item.get("category"),
                    item["published_at"],
                    item.get("content"),
                ))
                inserted += cur.rowcount

    print(f"[{source}] database: {inserted} new, {len(news) - inserted} already existed")
    return inserted