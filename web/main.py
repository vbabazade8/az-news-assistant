from datetime import date
from pathlib import Path

import markdown
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from psycopg.rows import dict_row

from scraper_job.utils.database import get_connection
from web.texts import LANGUAGES, TEXTS, format_day_month, format_full_date, format_weekday

WEB_DIR = Path(__file__).parent

app = FastAPI()

# CSS and other static files: web/static/style.css is served at /static/style.css
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")

# HTML templates: web/templates
templates = Jinja2Templates(directory=WEB_DIR / "templates")

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


# ---------- Database ----------

def load_digest(language, digest_date=None):
    """Return the digest for this language (latest, or for a date), or None if there is none."""
    sql_query = SELECT_LATEST_DIGEST_SQL
    params = (language,)
    if digest_date is not None:
        sql_query = SELECT_DIGEST_BY_DATE_SQL
        params = (language, digest_date)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql_query, params)
            return cur.fetchone()


def load_dates():
    """Return all dates that have digests, newest first: [{"digest_date": date}, ...]"""
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SELECT_DIGEST_DATES_SQL)
            return cur.fetchall()


def digest_to_html(content):
    """The digest is written in Markdown; the browser needs HTML.
    Links to news sites open in a new tab, so the reader doesn't lose the digest."""
    html = markdown.markdown(content)
    return html.replace("<a href=", '<a target="_blank" rel="noopener" href=')


# ---------- API (JSON) ----------

@app.get("/digest")
def get_digest(language: str = "en", digest_date: date | None = None):
    if language not in LANGUAGES:
        raise HTTPException(status_code=400, detail="Language must be en, az or ru")

    row = load_digest(language, digest_date)
    if row is None:
        raise HTTPException(status_code=404, detail="Digest not found")
    return row


@app.get("/dates")
def get_digest_dates():
    return load_dates()


# ---------- Website (HTML) ----------

@app.get("/", response_class=HTMLResponse)
def home(request: Request, language: str = "en", digest_date: date | None = None):
    # On the website we don't show an error for a wrong language, we just use English
    if language not in LANGUAGES:
        language = "en"

    digest = load_digest(language, digest_date)

    # Which day the page is about: the digest's day, or the day that was asked for
    shown_date = digest["digest_date"] if digest else digest_date

    archive = []
    for row in load_dates():
        day = row["digest_date"]
        archive.append({
            "value": day.isoformat(),
            "label": format_day_month(day, language),
            "current": day == shown_date,
        })

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "language": language,
            "languages": LANGUAGES,
            "texts": TEXTS[language],
            "digest_date": shown_date.isoformat() if shown_date else None,
            "date_title": format_full_date(shown_date, language) if shown_date else None,
            "weekday": format_weekday(shown_date, language) if shown_date else None,
            "content_html": digest_to_html(digest["content"]) if digest else None,
            "archive": archive,
        },
    )