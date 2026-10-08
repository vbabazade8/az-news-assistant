from scraper_job.utils.database import get_connection

from fastapi import FastAPI
from fastapi import HTTPException
from psycopg.rows import dict_row

from datetime import date

app = FastAPI()

SELECT_LATEST_DIGEST_SQL = """
    SELECT digest_date, language, content
    FROM digests
    WHERE language = %s
    ORDER BY digest_date DESC
    LIMIT 1
"""

SELECT_DIGEST_BY_DATE_SQL = """
    SELECT digest_date, language, content
    FROM digests
    WHERE language = %s
    AND digest_date = %s
"""

SELECT_DIGEST_DATES_SQL = """
    SELECT DISTINCT digest_date
    FROM digests
    ORDER BY digest_date DESC
"""

@app.get("/digest")
def get_digest(language: str = "en", digest_date: date | None = None):
    sql_query = SELECT_LATEST_DIGEST_SQL
    params = (language,)
    if digest_date is not None:
        sql_query = SELECT_DIGEST_BY_DATE_SQL
        params = (language, digest_date)
    if language not in ["en", "ru", "az"]:
        raise HTTPException(status_code=400, detail="Language must be en, az or ru")
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql_query, params)
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Digest not found")
    return row

@app.get("/dates")
def get_digest_dates():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SELECT_DIGEST_DATES_SQL)
            rows = cur.fetchall()
    return rows