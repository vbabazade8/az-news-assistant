# az-news-assistant

Daily AI news digests for busy executives. Scrapers collect fresh articles from Azerbaijani news sites, store them in a database, and once a day Gemini reads all news from the last 24 hours and writes an industry digest (for example, for investment or banking) in the role of a senior analyst — with a high-level summary and actionable insights. The digest is shown on a website in English, Azerbaijani and Russian.

**Why:** CEOs and analysts don't have time to follow news sites, but they need to know what happened in their industry.

## Status

| Part | Status |
|---|---|
| Scrapers for report.az, apa.az, axar.az | ✅ done |
| Neon (PostgreSQL) database | ✅ done |
| Digest job (Gemini API), EN / AZ / RU | ✅ done |
| LLM call logging (prompt + response) | ✅ done |
| GitHub Actions (automatic daily run) | ✅ done |
| Digest API (FastAPI) | ✅ done |
| Website (Jinja): EN / AZ / RU switch, archive | ✅ done |
| Deploy | ⏳ next |

## Architecture

```mermaid
flowchart LR
    subgraph daily["GitHub Actions — every day at 03:13 Baku time"]
        direction LR
        subgraph collect["1. Collect"]
            sites["News sites<br/>report.az · apa.az · axar.az"] -->|HTML pages| scrapers["Scrapers<br/>report · apa · axar"]
        end
        subgraph summarize["2. Summarize"]
            job["Digest job"] -->|"news from the last 24h<br/>+ analyst prompt"| gemini["Gemini API"]
            gemini -.->|"digest in EN / AZ / RU<br/>(JSON)"| job
        end
    end

    scrapers -->|save news| db[("Neon<br/>PostgreSQL")]
    db -->|news from the last 24h| job
    job -->|"save digests<br/>+ log the LLM call"| db

    db -->|digests| web["FastAPI<br/>website + API"]
    web --> reader(("CEO / analyst"))

    classDef done fill:#d9f5e3,stroke:#16a34a,color:#111
    classDef planned fill:#f3f4f6,stroke:#9ca3af,color:#555,stroke-dasharray:5 5
    class sites,scrapers,db,job,gemini,web done
    class reader planned
```

Green — done, gray — planned (the website is not deployed yet).

## News sources

| Site | News in 24h | How pages are loaded | Where the date comes from |
|---|---|---|---|
| report.az | ~100–245 | infinite scroll, cursor (`/infinity/index?date=...`) | `data-timestamp` on the news card |
| apa.az | ~70–80 | page number (`/all-news?page=N`) | date and time on the news card |
| axar.az | ~100–115 | page in the URL (`/latest/pageN/`) | JSON-LD `datePublished` on the article page |

Each scraper:
1. goes through the news list page by page until it reaches news older than 24 hours
2. skips duplicates
3. opens every article and extracts its full text
4. saves the result to `data/<site>.csv` and to the `news` table in Neon

`scraper_job/run_scrapers.py` runs all scrapers one after another. If one site fails, the others still run; the job fails only if every scraper failed. To add a new site, write its scraper and add one line to the `SCRAPERS` dictionary.

## Digest

The digest job (`digest_job/run_digest.py`):
1. loads news from the last 24 hours from Neon (~300–500 on a weekday)
2. builds a compact prompt: for each news only the source, time, title and the first paragraph (up to 300 characters). The full text of 500 news is ~180k tokens; the compact version is ~30k tokens
3. asks Gemini to act as a senior investment fund analyst, select only business-relevant news and write a digest with **Top stories**, **Market signals**, **Risks to watch** and **Actionable insights**, citing news numbers
4. gets the digest in English, Azerbaijani and Russian in **one request**, as JSON with a fixed schema (structured output), so the answer is always valid JSON
5. saves the full prompt and the raw answer to the `llm_calls` table, before parsing, so even a broken answer can be debugged
6. replaces news numbers like `[12, 40]` in the digest with Markdown links to the original articles, so every fact can be checked
7. saves one row per language to the `digests` table, linked to its LLM call; running it again on the same day updates the rows instead of adding new ones

If Gemini is overloaded (503) or rate-limited (429), the job waits 30 seconds and retries up to 3 times.

## Automatic runs (GitHub Actions)

`.github/workflows/daily-digest.yml` runs every day at 23:13 UTC (03:13 in Baku):
1. installs dependencies
2. runs all scrapers (`python -m scraper_job.run_scrapers`)
3. makes the digest (`python -m digest_job.run_digest`)
4. uploads the raw Gemini answer as a run artifact

It can also be started manually with the **Run workflow** button. `DATABASE_URL` and `GEMINI_API_KEY` are stored in the repository secrets.

GitHub often starts scheduled runs late (sometimes by hours), so the job starts early: even with a delay, the digest is usually ready by the morning.

## Website

Built with FastAPI and Jinja templates (`web/`).

- `/` — the latest digest
- `/?language=az` — switch language: `en`, `az` or `ru`
- `/?language=ru&digest_date=2026-10-07` — a digest from the archive

The digest is stored in Markdown and turned into HTML on the page. Links to the original articles open in a new tab. All texts of the website (in three languages) and the month and weekday names are in `web/texts.py` — to add a language, add it there.

## API

| Request | Returns |
|---|---|
| `GET /digest?language=en` | the latest digest in `en`, `az` or `ru` (default `en`) |
| `GET /digest?language=ru&digest_date=2026-10-07` | the digest for a specific date |
| `GET /dates` | all dates that have digests, newest first |

Errors: `400` for an unknown language, `404` if there is no digest.

Interactive documentation is available at `/docs`.

## Database

Three tables ([schema](scraper_job/sql/schema.sql)):

**`news`** — all scraped news from every source

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | primary key |
| `source` | `TEXT` | site name, for example `report.az` |
| `title` | `TEXT` | |
| `url` | `TEXT` | **unique** — the same news is never saved twice |
| `category` | `TEXT` | may be empty |
| `published_at` | `TIMESTAMPTZ` | when the news was published |
| `content` | `TEXT` | full article text (plain text, no HTML) |
| `scraped_at` | `TIMESTAMPTZ` | when we saved it, set by the database |

**`llm_calls`** — every call to the LLM: what we asked and what it answered

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | primary key |
| `task` | `TEXT` | what the call was for, for example `digest` (later also `chat`) |
| `industry` | `TEXT` | for example `investment` |
| `model` | `TEXT` | which Gemini model was used |
| `prompt` | `TEXT` | the full prompt we sent |
| `response` | `TEXT` | the raw answer from the model |
| `news_count` | `INTEGER` | how many news were in the prompt |
| `created_at` | `TIMESTAMPTZ` | when the call was made |

**`digests`** — AI-generated digests, one row per day, industry and language

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | primary key |
| `digest_date` | `DATE` | the day the digest is about |
| `industry` | `TEXT` | for example `investment` |
| `language` | `TEXT` | `en`, `az` or `ru` |
| `content` | `TEXT` | the digest in Markdown, with links to sources |
| `news_count` | `INTEGER` | how many news Gemini used |
| `model` | `TEXT` | which Gemini model wrote it |
| `llm_call_id` | `INTEGER` | the LLM call that produced this digest (`llm_calls.id`) |
| `created_at` | `TIMESTAMPTZ` | when it was generated |

`(digest_date, industry, language)` is unique.

## Project structure

```
az-news-assistant/
├── .github/
│   └── workflows/
│       └── daily-digest.yml   # daily run: scrapers + digest
├── scraper_job/
│   ├── config.py              # shared settings: headers, timezone, hours back, max pages
│   ├── run_scrapers.py        # runs all scrapers one after another
│   ├── sql/
│   │   └── schema.sql         # creates the news, llm_calls and digests tables
│   ├── utils/
│   │   ├── helpers.py         # shared functions: fetch_html, save_csv
│   │   └── database.py        # Neon: save_news, get_recent_news, save_llm_call, save_digests
│   └── scrapers/
│       ├── report_scraper.py  # report.az
│       ├── apa_scraper.py     # apa.az
│       └── axar_scraper.py    # axar.az
├── digest_job/
│   ├── gemini.py              # Gemini API call with retries
│   ├── prompt.py              # compact news block + analyst prompt
│   ├── sources.py             # turns news numbers into links to the original articles
│   └── run_digest.py          # loads news, asks Gemini, saves digests
├── web/
│   ├── main.py                # FastAPI: website page, /digest and /dates
│   ├── texts.py               # website texts in EN / AZ / RU, month and weekday names
│   ├── templates/
│   │   └── index.html         # the page (Jinja template)
│   └── static/
│       └── style.css          # the design
├── requirements.txt
└── README.md
```

## Run locally

1. Install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

2. Create a free PostgreSQL database on [Neon](https://neon.tech) and run `scraper_job/sql/schema.sql` in its SQL Editor.

3. Get a free Gemini API key in [Google AI Studio](https://aistudio.google.com).

4. Create a `.env` file in the project root (it is in `.gitignore`, never commit it):

```
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
GEMINI_API_KEY=your-gemini-api-key
```

5. Collect news and make a digest:

```bash
python -m scraper_job.run_scrapers
python -m digest_job.run_digest
```

6. Start the website:

```bash
uvicorn web.main:app --reload
```

Open http://127.0.0.1:8000 for the website, or http://127.0.0.1:8000/docs for the API.