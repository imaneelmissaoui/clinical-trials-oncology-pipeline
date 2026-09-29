"""Command-line orchestration for the complete local data pipeline."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .api import fetch_studies
from .dashboard import export_dashboard
from .database import load_studies
from .transform import dashboard_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def _run_dbt() -> None:
    dbt_executable = os.getenv("DBT_EXECUTABLE", "dbt")
    executable_path = shutil.which(dbt_executable)
    command = [executable_path] if executable_path else [sys.executable, "-m", "dbt.cli.main"]
    env = os.environ.copy()
    result = subprocess.run(
        [*command, "build", "--profiles-dir", str(PROJECT_ROOT / "dbt")],
        cwd=PROJECT_ROOT / "dbt",
        env=env,
        check=False,
    )
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, result.args)


def run_pipeline(args: argparse.Namespace) -> None:
    _load_environment()
    query_condition = args.condition or os.getenv("CTG_QUERY_CONDITION", "lymphoma")
    page_size = args.page_size or int(os.getenv("CTG_PAGE_SIZE", "250"))
    max_studies = args.limit if args.limit is not None else int(os.getenv("CTG_MAX_STUDIES", "1000"))

    print(f"Fetching ClinicalTrials.gov studies for condition: {query_condition}")
    batch = fetch_studies(query_condition, page_size, max_studies)
    print(
        f"Fetched {len(batch.studies):,} unique studies across {batch.page_count} page(s). "
        f"API query total: {batch.api_total_count if batch.api_total_count is not None else 'not returned'}"
    )
    run_id, inserted, skipped = load_studies(
        batch.studies,
        query_condition,
        batch.api_total_count,
        batch.page_count,
    )
    print(f"Bronze load complete · run {run_id} · inserted {inserted:,} · skipped {skipped:,}")
    print("Building Silver and Gold models and running dbt tests...")
    _run_dbt()
    print("dbt build completed successfully.")

    if args.dashboard_output:
        payload = export_dashboard(Path(args.dashboard_output).expanduser().resolve())
        print(f"Dashboard snapshot exported: {args.dashboard_output} ({payload['metadata']['study_count']:,} studies)")


def preview_dashboard(args: argparse.Namespace) -> None:
    """Fetch a public-record preview without requiring a local database."""

    _load_environment()
    condition = args.condition or os.getenv("CTG_QUERY_CONDITION", "lymphoma")
    page_size = args.page_size or int(os.getenv("CTG_PAGE_SIZE", "250"))
    max_studies = args.limit if args.limit is not None else int(os.getenv("CTG_MAX_STUDIES", "1000"))
    batch = fetch_studies(condition, page_size, max_studies)
    payload = dashboard_payload(
        batch.studies,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        query_condition=condition,
        api_total_count=batch.api_total_count,
        page_count=batch.page_count,
    )
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    import json

    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Public dashboard preview exported: {output} ({len(payload['studies']):,} studies)")
    print("Run the complete pipeline and export-dashboard command to replace this with a Gold-layer snapshot.")


def export_from_gold(args: argparse.Namespace) -> None:
    _load_environment()
    payload = export_dashboard(Path(args.output).expanduser().resolve())
    print(f"Gold dashboard snapshot exported: {args.output} ({payload['metadata']['study_count']:,} studies)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="clinical-trials-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Fetch studies, load Bronze, build dbt models and optionally export the dashboard.")
    run.add_argument("--condition", help="ClinicalTrials.gov condition query; defaults to CTG_QUERY_CONDITION or lymphoma.")
    run.add_argument("--limit", type=int, help="Maximum unique studies to fetch; use 0 for all matching studies.")
    run.add_argument("--page-size", type=int, help="API page size from 1 to 1000.")
    run.add_argument("--dashboard-output", help="Optional path for a Gold-layer JSON dashboard snapshot.")
    run.set_defaults(func=run_pipeline)

    preview = subparsers.add_parser("preview", help="Create a public API dashboard snapshot without PostgreSQL/dbt.")
    preview.add_argument("--condition", help="ClinicalTrials.gov condition query.")
    preview.add_argument("--limit", type=int, help="Maximum unique studies; use 0 for all matching studies.")
    preview.add_argument("--page-size", type=int, help="API page size from 1 to 1000.")
    preview.add_argument("--output", required=True, help="Destination JSON path.")
    preview.set_defaults(func=preview_dashboard)

    export = subparsers.add_parser("export-dashboard", help="Export dashboard JSON from the Gold warehouse.")
    export.add_argument("--output", required=True, help="Destination JSON path.")
    export.set_defaults(func=export_from_gold)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
