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

-- Every call to the LLM: what we asked and what it answered
CREATE TABLE IF NOT EXISTS llm_calls (
    id           SERIAL PRIMARY KEY,
    task         TEXT NOT NULL,                       -- what the call was for, for example 'digest'
    industry     TEXT,                                -- for example 'investment'
    model        TEXT NOT NULL,                       -- which Gemini model was used
    prompt       TEXT NOT NULL,                       -- the full prompt we sent
    response     TEXT,                                -- the raw answer from the model
    news_count   INTEGER,                             -- how many news were in the prompt
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table for AI-generated digests: one row = one digest for one day, one industry, one language
CREATE TABLE IF NOT EXISTS digests (
    id           SERIAL PRIMARY KEY,
    digest_date  DATE NOT NULL,                       -- the day the digest is about
    industry     TEXT NOT NULL,                       -- for example 'investment'
    language     TEXT NOT NULL,                       -- 'en', 'az' or 'ru'
    content      TEXT NOT NULL,                       -- the digest text with links to sources
    news_count   INTEGER,                             -- how many news Gemini used
    model        TEXT,                                -- which Gemini model wrote it
    llm_call_id  INTEGER REFERENCES llm_calls(id),    -- the LLM call that produced this digest
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (digest_date, industry, language)          -- only one digest per day, industry and language
);