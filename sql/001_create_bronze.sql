CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.raw_studies (
    record_id BIGSERIAL PRIMARY KEY,
    nct_id TEXT NOT NULL,
    source_payload JSONB NOT NULL,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_updated_at TEXT,
    ingestion_run_id TEXT NOT NULL,

    CONSTRAINT uq_raw_study_run
        UNIQUE (nct_id, ingestion_run_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_studies_nct_id
    ON bronze.raw_studies (nct_id);