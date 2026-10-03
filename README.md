# az-news-assistant

Ask questions about today's Azerbaijani news. Scrapers collect fresh articles from several news sites, store them in a database, and Gemini answers questions using all news from the last 24 hours (CAG — cache-augmented generation).

## Status

| Part | Status |
|---|---|
| Scrapers for report.az, apa.az, axar.az | ✅ done |
| Neon (PostgreSQL) database | ⏳ next |
| Gemini API (CAG) | ⏳ planned |
| FastAPI backend | ⏳ planned |
| Frontend | ⏳ planned |
| GitHub Actions (automatic scraping) | ⏳ planned |

## Architecture

```mermaid
flowchart LR
    subgraph collect["News collection — automatic, 3 times a day"]
        sites["News sites<br/>report.az · apa.az · axar.az"] -->|HTML pages| scrapers["Scrapers<br/>report · apa · axar"]
    end

    scrapers -->|save news| db[("Neon<br/>PostgreSQL")]

    subgraph answer["Answering a question — every time a user asks"]
        user((User)) -->|1. question| front[Frontend]
        front -->|2. question| api[FastAPI]
        api -->|3. get news from the last 24h| db
        db -.->|4. news| api
        api -->|5. news + question| gemini[Gemini API]
        gemini -.->|6. answer| api
        api -.->|7. answer| front
        front -.->|8. answer| user
    end

    classDef done fill:#d9f5e3,stroke:#16a34a,color:#111
    classDef planned fill:#f3f4f6,stroke:#9ca3af,color:#555,stroke-dasharray:5 5
    class sites,scrapers done
    class db,user,front,api,gemini planned
```

Solid arrow — request, dashed arrow — response. Green — done, gray — planned.

## News sources

| Site | News in 24h | How pages are loaded | Where the date comes from |
|---|---|---|---|
| report.az | ~135–245 | infinite scroll, cursor (`/infinity/index?date=...`) | `data-timestamp` on the news card |
| apa.az | ~70 | page number (`/all-news?page=N`) | date and time on the news card |
| axar.az | ~115 | page in the URL (`/latest/pageN/`) | JSON-LD `datePublished` on the article page |

Each scraper:
1. goes through the news list page by page until it reaches news older than 24 hours
2. skips duplicates
3. opens every article and extracts its full text
4. saves the result to `data/<site>.csv`

## Project structure

```
az-news-assistant/
├── scraper_job/
│   ├── config.py              # shared settings: headers, timezone, hours back, max pages
│   ├── utils/
│   │   └── helpers.py         # shared functions: fetch_html, save_csv
│   └── scrapers/
│       ├── report_scraper.py  # report.az
│       ├── apa_scraper.py     # apa.az
│       └── axar_scraper.py    # axar.az
├── requirements.txt
└── README.md
```

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python -m scraper_job.scrapers.report_scraper
python -m scraper_job.scrapers.apa_scraper
python -m scraper_job.scrapers.axar_scraper
```

Results are saved to the `data/` folder (not tracked by git).