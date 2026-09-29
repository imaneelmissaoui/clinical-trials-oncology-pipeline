"""Client for the public ClinicalTrials.gov API v2 studies endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


API_URL = "https://clinicaltrials.gov/api/v2/studies"
USER_AGENT = "clinical-trials-oncology-pipeline/1.0 (public portfolio project)"


@dataclass(frozen=True)
class StudyBatch:
    studies: list[dict[str, Any]]
    api_total_count: int | None
    page_count: int
    query_condition: str


def fetch_studies(
    query_condition: str = "lymphoma",
    page_size: int = 250,
    max_studies: int = 1000,
    timeout_seconds: int = 60,
    session: requests.Session | None = None,
) -> StudyBatch:
    """Fetch a bounded, cursor-paginated set of complete study records.

    Set ``max_studies`` to 0 to follow every page returned by the query.
    ClinicalTrials.gov permits up to 1,000 records per response page.
    """

    if not query_condition.strip():
        raise ValueError("The condition query must not be empty.")
    if not 1 <= page_size <= 1000:
        raise ValueError("page_size must be between 1 and 1000.")
    if max_studies < 0:
        raise ValueError("max_studies must be 0 (unlimited) or a positive integer.")

    client = session or requests.Session()
    client.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    studies: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    next_page_token: str | None = None
    api_total_count: int | None = None
    page_count = 0

    while True:
        params: dict[str, Any] = {
            "query.cond": query_condition,
            "pageSize": page_size,
            "format": "json",
            "countTotal": "true",
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        response = client.get(API_URL, params=params, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        page_count += 1
        if api_total_count is None:
            raw_total = payload.get("totalCount")
            api_total_count = int(raw_total) if raw_total is not None else None

        for study in payload.get("studies", []):
            nct_id = (
                study.get("protocolSection", {})
                .get("identificationModule", {})
                .get("nctId")
            )
            if not nct_id or nct_id in seen_ids:
                continue
            studies.append(study)
            seen_ids.add(nct_id)
            if max_studies and len(studies) >= max_studies:
                break

        if max_studies and len(studies) >= max_studies:
            break
        next_page_token = payload.get("nextPageToken")
        if not next_page_token:
            break

    return StudyBatch(
        studies=studies,
        api_total_count=api_total_count,
        page_count=page_count,
        query_condition=query_condition,
    )
