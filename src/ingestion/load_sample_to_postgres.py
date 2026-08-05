from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


# Resolve the root directory of the project.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Path to the local environment configuration file.
ENV_PATH = PROJECT_ROOT / ".env"

# Path to the saved ClinicalTrials.gov API sample.
INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lymphoma_studies_sample.json"
)


def get_required_env_variable(name: str) -> str:
    """Return a required environment variable or raise a clear error."""

    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Required environment variable is missing: {name}"
        )

    return value


def get_nct_id(study: dict) -> str | None:
    """Extract the unique ClinicalTrials.gov identifier."""

    protocol_section = study.get("protocolSection", {})

    identification_module = protocol_section.get(
        "identificationModule",
        {},
    )

    return identification_module.get("nctId")


def get_source_updated_at(study: dict) -> str | None:
    """Extract the last published update date from one study."""

    protocol_section = study.get("protocolSection", {})

    status_module = protocol_section.get(
        "statusModule",
        {},
    )

    last_update_struct = status_module.get(
        "lastUpdatePostDateStruct",
        {},
    )

    return last_update_struct.get("date")


def main() -> None:
    """Load the saved clinical trial sample into PostgreSQL Bronze."""

    # Load the current values from the local .env file.
    load_dotenv(ENV_PATH, override=True)

    # Stop execution with a clear message if the source file is missing.
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Run explore_api.py first."
        )

    # Convert the saved JSON text into Python dictionaries and lists.
    payload = json.loads(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    studies = payload.get("studies", [])

    # Exit cleanly when the API response contains no studies.
    if not studies:
        print("No studies found in the input file.")
        return

    # Create one identifier shared by every row loaded in this execution.
    ingestion_run_id = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    # Read the database connection settings from environment variables.
    connection_parameters = {
        "host": get_required_env_variable("POSTGRES_HOST"),
        "port": get_required_env_variable("POSTGRES_PORT"),
        "dbname": get_required_env_variable("POSTGRES_DB"),
        "user": get_required_env_variable("POSTGRES_USER"),
        "password": get_required_env_variable(
            "POSTGRES_PASSWORD"
        ),
    }

    # Insert one complete clinical trial payload into the Bronze table.
    insert_query = """
        INSERT INTO bronze.raw_studies (
            nct_id,
            source_payload,
            source_updated_at,
            ingestion_run_id
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (nct_id, ingestion_run_id)
        DO NOTHING;
    """

    inserted_count = 0
    skipped_count = 0

    print(f"Input file: {INPUT_PATH}")
    print(f"Studies found: {len(studies)}")
    print(f"Ingestion run ID: {ingestion_run_id}")
    print(
        "Database target: "
        f"{connection_parameters['host']}:"
        f"{connection_parameters['port']}/"
        f"{connection_parameters['dbname']}"
    )
    print("Connecting to PostgreSQL...")

    # Use one database transaction for the complete ingestion run.
    with psycopg.connect(
        **connection_parameters
    ) as connection:
        with connection.cursor() as cursor:
            for study in studies:
                nct_id = get_nct_id(study)

                # An NCT ID is required to identify and track each study.
                if not nct_id:
                    print("Skipping study without an NCT ID.")
                    skipped_count += 1
                    continue

                source_updated_at = get_source_updated_at(
                    study
                )

                # Jsonb converts the Python dictionary into PostgreSQL JSONB.
                cursor.execute(
                    insert_query,
                    (
                        nct_id,
                        Jsonb(study),
                        source_updated_at,
                        ingestion_run_id,
                    ),
                )

                if cursor.rowcount == 1:
                    inserted_count += 1
                    print(f"Inserted: {nct_id}")
                else:
                    skipped_count += 1
                    print(f"Skipped duplicate: {nct_id}")

    print()
    print("Bronze loading completed.")
    print(f"Inserted rows: {inserted_count}")
    print(f"Skipped rows: {skipped_count}")


if __name__ == "__main__":
    main()