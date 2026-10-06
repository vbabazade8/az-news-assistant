import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

INSERT_NEWS_SQL = """
    INSERT INTO news (source, title, url, category, published_at, content)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (url) DO NOTHING
"""

SELECT_RECENT_NEWS_SQL = """
    SELECT source, title, url, category, published_at, content
    FROM news
    WHERE published_at >= NOW() - %s * INTERVAL '1 hour'
    ORDER BY published_at DESC
"""

INSERT_LLM_CALL_SQL = """
    INSERT INTO llm_calls (task, industry, model, prompt, response, news_count)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
"""

UPSERT_DIGEST_SQL = """
    INSERT INTO digests (digest_date, industry, language, content, news_count, model, llm_call_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (digest_date, industry, language) DO UPDATE SET
        content     = EXCLUDED.content,
        news_count  = EXCLUDED.news_count,
        model       = EXCLUDED.model,
        llm_call_id = EXCLUDED.llm_call_id,
        created_at  = NOW()
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


def get_recent_news(hours):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SELECT_RECENT_NEWS_SQL, (hours,))
            return cur.fetchall()


def save_llm_call(task, industry, model, prompt, response, news_count):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(INSERT_LLM_CALL_SQL, (task, industry, model, prompt, response, news_count))
            llm_call_id = cur.fetchone()[0]
    print(f"[llm] saved call #{llm_call_id} ({task}, {len(prompt)} prompt chars)")
    return llm_call_id


def save_digests(digest_date, industry, texts, news_count, model, llm_call_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            for language, content in texts.items():
                cur.execute(UPSERT_DIGEST_SQL, (
                    digest_date,
                    industry,
                    language,
                    content,
                    news_count,
                    model,
                    llm_call_id,
                ))
    print(f"[digest] saved {len(texts)} languages for {industry}, {digest_date}")