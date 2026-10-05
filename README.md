# az-news-assistant

Daily AI news digests for busy executives. Scrapers collect fresh articles from Azerbaijani news sites, store them in a database, and once a day Gemini reads all news from the last 24 hours and writes an industry digest (for example, for investment or banking) in the role of a senior analyst — with a high-level summary and actionable insights. The digest is shown on a website.

**Why:** CEOs and analysts don't have time to follow news sites, but they need to know what happened in their industry.

## Status

| Part | Status |
|---|---|
| Scrapers for report.az, apa.az, axar.az | ✅ done |
| Neon (PostgreSQL) database | ✅ done |
| Digest job (Gemini API), EN / AZ / RU | ✅ done |
| Website | ⏳ next |
| GitHub Actions (automatic runs) | ⏳ planned |

## Architecture

```mermaid
flowchart LR
    subgraph collect["1. Collect — automatic, several times a day"]
        sites["News sites<br/>report.az · apa.az · axar.az"] -->|HTML pages| scrapers["Scrapers<br/>report · apa · axar"]
    end

    scrapers -->|save news| db[("Neon<br/>PostgreSQL")]

    subgraph summarize["2. Summarize — automatic, once a day"]
        job["Digest job"] -->|"news from the last 24h<br/>+ analyst prompt"| gemini["Gemini API"]
        gemini -.->|"digest in EN / AZ / RU<br/>(JSON)"| job
    end

    db -->|news from the last 24h| job
    job -->|save digests| db

    db -->|latest digests| web["Website"]
    web --> reader(("CEO / analyst"))

    classDef done fill:#d9f5e3,stroke:#16a34a,color:#111
    classDef planned fill:#f3f4f6,stroke:#9ca3af,color:#555,stroke-dasharray:5 5
    class sites,scrapers,db,job,gemini done
    class web,reader planned
```

Green — done, gray — planned.

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

## Digest

The digest job (`digest_job/run_digest.py`):
1. loads news from the last 24 hours from Neon (~500 on a weekday)
2. builds a compact prompt: for each news only the source, time, title and the first paragraph (up to 300 characters). The full text of 500 news is ~180k tokens; the compact version is ~30k tokens
3. asks Gemini to act as a senior investment fund analyst, select only business-relevant news and write a digest with **Top stories**, **Market signals**, **Risks to watch** and **Actionable insights**, citing news numbers
4. gets the digest in English, Azerbaijani and Russian in **one request**, as JSON with a fixed schema (structured output), so the answer is always valid JSON
5. replaces news numbers like `[12, 40]` in the digest with Markdown links to the original articles, so every fact can be checked
6. saves one row per language to the `digests` table; running it again on the same day updates the rows instead of adding new ones

If Gemini is overloaded (503) or rate-limited (429), the job waits 30 seconds and retries up to 3 times.

## Database

Two tables ([schema](scraper_job/sql/schema.sql)):

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
| `created_at` | `TIMESTAMPTZ` | when it was generated |

`(digest_date, industry, language)` is unique.

## Project structure

```
az-news-assistant/
├── scraper_job/
│   ├── config.py              # shared settings: headers, timezone, hours back, max pages
│   ├── sql/
│   │   └── schema.sql         # creates the news and digests tables
│   ├── utils/
│   │   ├── helpers.py         # shared functions: fetch_html, save_csv
│   │   └── database.py        # Neon: save_news, get_recent_news, save_digests
│   └── scrapers/
│       ├── report_scraper.py  # report.az
│       ├── apa_scraper.py     # apa.az
│       └── axar_scraper.py    # axar.az
├── digest_job/
│   ├── gemini.py              # Gemini API call with retries
│   ├── prompt.py              # compact news block + analyst prompt
│   ├── sources.py             # turns news numbers into links to the original articles
│   └── run_digest.py          # loads news, asks Gemini, saves digests
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
python -m scraper_job.scrapers.report_scraper
python -m scraper_job.scrapers.apa_scraper
python -m scraper_job.scrapers.axar_scraper

python -m digest_job.run_digest
```