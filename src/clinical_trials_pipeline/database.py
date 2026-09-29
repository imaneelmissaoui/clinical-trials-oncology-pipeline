"""PostgreSQL connection and Bronze loading helpers."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def connection_parameters() -> dict[str, Any]:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5433")),
        "dbname": os.getenv("POSTGRES_DB", "clinical_trials"),
        "user": os.getenv("POSTGRES_USER", "clinical_user"),
        "password": os.getenv("POSTGRES_PASSWORD", "change_me"),
    }


def ensure_bronze_schema(connection: psycopg.Connection[Any]) -> None:
    """Create the raw table and safely extend the starter schema if needed."""

    statements = [
        "CREATE SCHEMA IF NOT EXISTS bronze",
        """CREATE TABLE IF NOT EXISTS bronze.raw_studies (
            record_id BIGSERIAL PRIMARY KEY,
            nct_id TEXT NOT NULL,
            source_payload JSONB NOT NULL,
            extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            source_updated_at TEXT,
            ingestion_run_id TEXT NOT NULL,
            api_query TEXT NOT NULL DEFAULT 'lymphoma',
            CONSTRAINT uq_raw_study_run UNIQUE (nct_id, ingestion_run_id)
        )""",
        """CREATE TABLE IF NOT EXISTS bronze.ingestion_runs (
            ingestion_run_id TEXT PRIMARY KEY,
            started_at TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ NOT NULL,
            query_condition TEXT NOT NULL,
            api_total_count INTEGER,
            page_count INTEGER NOT NULL,
            fetched_count INTEGER NOT NULL,
            inserted_count INTEGER NOT NULL,
            skipped_count INTEGER NOT NULL
        )""",
        "ALTER TABLE bronze.raw_studies ADD COLUMN IF NOT EXISTS api_query TEXT NOT NULL DEFAULT 'lymphoma'",
        "CREATE INDEX IF NOT EXISTS idx_raw_studies_nct_id ON bronze.raw_studies (nct_id)",
        "CREATE INDEX IF NOT EXISTS idx_raw_studies_extracted_at ON bronze.raw_studies (extracted_at)",
    ]
    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def source_updated_at(study: dict[str, Any]) -> str | None:
    return (
        study.get("protocolSection", {})
        .get("statusModule", {})
        .get("lastUpdatePostDateStruct", {})
        .get("date")
    )


def load_studies(
    studies: list[dict[str, Any]],
    query_condition: str,
    api_total_count: int | None,
    page_count: int,
) -> tuple[str, int, int]:
    """Insert one immutable Bronze snapshot per study and run."""

    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%S%fZ")
    inserted = 0
    skipped = 0
    insert_sql = """
        INSERT INTO bronze.raw_studies
            (nct_id, source_payload, source_updated_at, ingestion_run_id, api_query)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (nct_id, ingestion_run_id) DO NOTHING
    """

    with psycopg.connect(**connection_parameters()) as connection:
        ensure_bronze_schema(connection)
        with connection.cursor() as cursor:
            for study in studies:
                nct_id = (
                    study.get("protocolSection", {})
                    .get("identificationModule", {})
                    .get("nctId")
                )
                if not nct_id:
                    skipped += 1
                    continue
                cursor.execute(
                    insert_sql,
                    (nct_id, Jsonb(study), source_updated_at(study), run_id, query_condition),
                )
                inserted += cursor.rowcount
                skipped += 1 - cursor.rowcount
            cursor.execute(
                """INSERT INTO bronze.ingestion_runs (
                       ingestion_run_id, started_at, completed_at, query_condition,
                       api_total_count, page_count, fetched_count, inserted_count, skipped_count
                   ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    run_id,
                    started_at,
                    datetime.now(timezone.utc),
                    query_condition,
                    api_total_count,
                    page_count,
                    len(studies),
                    inserted,
                    skipped,
                ),
            )
    return run_id, inserted, skipped
