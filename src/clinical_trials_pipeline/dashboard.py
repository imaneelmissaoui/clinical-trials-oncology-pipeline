"""Export a small read-only dashboard snapshot from the Gold warehouse."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg

from .database import connection_parameters


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def export_dashboard(output_path: Path) -> dict[str, Any]:
    """Write dashboard-ready trial metadata from the dbt Gold models."""

    query = """
        SELECT
            f.nct_id,
            f.brief_title,
            f.study_type,
            f.overall_status,
            f.phase,
            f.sponsor_name,
            f.enrollment_count,
            f.enrollment_type,
            f.start_date,
            f.completion_date,
            f.study_first_post_date,
            f.last_update_date,
            f.has_results,
            f.duration_months,
            f.location_count,
            f.is_imaging_related,
            f.imaging_signals,
            COALESCE(c.conditions, '[]'::jsonb) AS conditions,
            COALESCE(g.countries, '[]'::jsonb) AS countries,
            COALESCE(i.interventions, '[]'::jsonb) AS interventions
        FROM gold.fct_trials AS f
        LEFT JOIN (
            SELECT nct_id, jsonb_agg(condition_name ORDER BY condition_name) AS conditions
            FROM gold.bridge_trial_conditions GROUP BY nct_id
        ) AS c USING (nct_id)
        LEFT JOIN (
            SELECT nct_id, jsonb_agg(country_name ORDER BY country_name) AS countries
            FROM gold.bridge_trial_countries GROUP BY nct_id
        ) AS g USING (nct_id)
        LEFT JOIN (
            SELECT nct_id,
                   jsonb_agg(jsonb_build_object('name', intervention_name, 'type', intervention_type)
                             ORDER BY intervention_name) AS interventions
            FROM gold.bridge_trial_interventions GROUP BY nct_id
        ) AS i USING (nct_id)
        WHERE f.ingestion_run_id = %s
        ORDER BY f.last_update_date DESC NULLS LAST, f.nct_id
    """

    with psycopg.connect(**connection_parameters()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT ingestion_run_id, query_condition, api_total_count, page_count, completed_at
                   FROM bronze.ingestion_runs
                   ORDER BY completed_at DESC
                   LIMIT 1"""
            )
            latest_run = cursor.fetchone()
            if latest_run is None:
                raise RuntimeError("No completed ingestion run was found in bronze.ingestion_runs.")
            run_id, query_condition, api_total_count, page_count, completed_at = latest_run
            cursor.execute(query, (run_id,))
            columns = [description.name for description in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.execute(
                "SELECT MAX(last_update_date), COUNT(*) FROM gold.fct_trials WHERE ingestion_run_id = %s",
                (run_id,),
            )
            max_update, total = cursor.fetchone()

    payload = {
        "metadata": {
            "source": "ClinicalTrials.gov API v2",
            "source_url": "https://clinicaltrials.gov/",
            "query": f"Condition: {query_condition}",
            "generated_at": completed_at.isoformat(timespec="seconds"),
            "study_count": int(total),
            "api_total_count": api_total_count,
            "page_count": page_count,
            "source_last_update": max_update,
            "scope_note": "Dashboard snapshot exported from the Gold warehouse; public registry records are not patient-level data.",
        },
        "studies": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )
    return payload
