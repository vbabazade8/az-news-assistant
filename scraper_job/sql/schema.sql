-- Table for all scraped news from every source
CREATE TABLE IF NOT EXISTS news (
    id           SERIAL PRIMARY KEY,
    source       TEXT NOT NULL,                       -- site name, for example 'report.az'
    title        TEXT NOT NULL,
    url          TEXT NOT NULL UNIQUE,                -- unique, so the same news is never saved twice
    category     TEXT,
    published_at TIMESTAMPTZ NOT NULL,                -- when the news was published (with timezone)
    content      TEXT,
    scraped_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()   -- when we saved it, set by the database
);


CREATE TABLE IF NOT EXISTS digests (
    id           SERIAL PRIMARY KEY,
    digest_date  DATE NOT NULL,
    industry     TEXT NOT NULL,
    language     TEXT NOT NULL,
    content      TEXT NOT NULL,
    news_count   INTEGER,
    model        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (digest_date, industry, language)
);