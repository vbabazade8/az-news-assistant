from scraper_job.utils.database import get_connection

from fastapi import FastAPI
from psycopg.rows import dict_row

app = FastAPI()

SELECT_LATEST_DIGEST_SQL = """
    SELECT digest_date, language, content
    FROM digests
    WHERE language = %s
    ORDER BY digest_date DESC
    LIMIT 1
"""

@app.get("/digest")
def get_digest(language: str = "en"):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SELECT_LATEST_DIGEST_SQL, (language,))
            row = cur.fetchone()
    return row