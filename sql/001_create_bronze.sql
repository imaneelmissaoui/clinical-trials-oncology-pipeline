CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.raw_studies (
    record_id BIGSERIAL PRIMARY KEY,
    nct_id TEXT NOT NULL,
    source_payload JSONB NOT NULL,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_updated_at TEXT,
    ingestion_run_id TEXT NOT NULL,
    api_query TEXT NOT NULL DEFAULT 'lymphoma',
    CONSTRAINT uq_raw_study_run UNIQUE (nct_id, ingestion_run_id)
);

CREATE TABLE IF NOT EXISTS bronze.ingestion_runs (
    ingestion_run_id TEXT PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL,
    query_condition TEXT NOT NULL,
    api_total_count INTEGER,
    page_count INTEGER NOT NULL,
    fetched_count INTEGER NOT NULL,
    inserted_count INTEGER NOT NULL,
    skipped_count INTEGER NOT NULL
);

-- Also supports databases created from the earlier Bronze-only project version.
ALTER TABLE bronze.raw_studies
    ADD COLUMN IF NOT EXISTS api_query TEXT NOT NULL DEFAULT 'lymphoma';

CREATE INDEX IF NOT EXISTS idx_raw_studies_nct_id
    ON bronze.raw_studies (nct_id);

CREATE INDEX IF NOT EXISTS idx_raw_studies_extracted_at
    ON bronze.raw_studies (extracted_at);
