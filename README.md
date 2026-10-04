# az-news-assistant

Daily AI news digests for busy executives. Scrapers collect fresh articles from Azerbaijani news sites, store them in a database, and once a day Gemini reads all news from the last 24 hours and writes an industry digest (for example, for investment or banking) in the role of a senior analyst — with a high-level summary and actionable insights. The digest is shown on a website.

**Why:** CEOs and analysts don't have time to follow news sites, but they need to know what happened in their industry.

## Status

| Part | Status |
|---|---|
| Scrapers for report.az, apa.az, axar.az | ✅ done |
| Neon (PostgreSQL) database | ✅ done |
| Digest job (Gemini API) | ⏳ next |
| Website | ⏳ planned |
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
        gemini -.->|"summary +<br/>actionable insights"| job
    end

    db -->|news from the last 24h| job
    job -->|save digest| db

    db -->|latest digests| web["Website"]
    web --> reader(("CEO / analyst"))

    classDef done fill:#d9f5e3,stroke:#16a34a,color:#111
    classDef planned fill:#f3f4f6,stroke:#9ca3af,color:#555,stroke-dasharray:5 5
    class sites,scrapers,db done
    class job,gemini,web,reader planned
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

## Database

One table, `news`, for all sources ([schema](scraper_job/sql/schema.sql)):

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | primary key |
| `source` | `TEXT` | site name, for example `report.az` |
| `title` | `TEXT` | |
| `url` | `TEXT` | **unique** — the same news is never saved twice |
| `category` | `TEXT` | may be empty |
| `published_at` | `TIMESTAMPTZ` | when the news was published |
| `content` | `TEXT` | full article text |
| `scraped_at` | `TIMESTAMPTZ` | when we saved it, set by the database |

Scrapers run several times a day, so the same article is found many times. `INSERT ... ON CONFLICT (url) DO NOTHING` skips news that are already in the table.

## Project structure

```
az-news-assistant/
├── scraper_job/
│   ├── config.py              # shared settings: headers, timezone, hours back, max pages
│   ├── sql/
│   │   └── schema.sql         # creates the news table
│   ├── utils/
│   │   ├── helpers.py         # shared functions: fetch_html, save_csv
│   │   └── database.py        # connection to Neon, save_news
│   └── scrapers/
│       ├── report_scraper.py  # report.az
│       ├── apa_scraper.py     # apa.az
│       └── axar_scraper.py    # axar.az
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

3. Create a `.env` file in the project root (it is in `.gitignore`, never commit it):

```
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

4. Run the scrapers:

```bash
python -m scraper_job.scrapers.report_scraper
python -m scraper_job.scrapers.apa_scraper
python -m scraper_job.scrapers.axar_scraper
```

News are saved to Neon and to the `data/` folder (CSV, not tracked by git).