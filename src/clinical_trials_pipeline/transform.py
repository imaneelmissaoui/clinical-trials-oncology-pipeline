"""Small, explicit transformations shared by preview and dashboard exports."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any


IMAGING_TERMS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("PET / PET-CT", re.compile(r"\bpet(?:\s*/\s*ct|[- ]?ct)?\b", re.I)),
    ("MRI", re.compile(r"\b(mri|magnetic resonance imaging)\b", re.I)),
    ("CT", re.compile(r"\b(ct scan|computed tomography)\b", re.I)),
    ("Imaging", re.compile(r"\b(imaging|radiolog(?:y|ic))\b", re.I)),
    ("Ultrasound", re.compile(r"\b(ultrasound|sonograph(?:y|ic))\b", re.I)),
)


def _module(study: dict[str, Any], name: str) -> dict[str, Any]:
    return study.get("protocolSection", {}).get(name, {}) or {}


def _date(value: Any) -> str | None:
    """Normalize complete and partial ClinicalTrials.gov dates to ISO dates."""

    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if re.fullmatch(r"\d{4}", candidate):
        candidate = f"{candidate}-01-01"
    elif re.fullmatch(r"\d{4}-\d{2}", candidate):
        candidate = f"{candidate}-01"
    elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return None
    try:
        return date.fromisoformat(candidate).isoformat()
    except ValueError:
        return None


def extract_trial(study: dict[str, Any]) -> dict[str, Any] | None:
    """Flatten the fields used by the Gold models and hosted dashboard."""

    identification = _module(study, "identificationModule")
    status = _module(study, "statusModule")
    sponsor_module = _module(study, "sponsorCollaboratorsModule")
    condition_module = _module(study, "conditionsModule")
    design = _module(study, "designModule")
    intervention_module = _module(study, "armsInterventionsModule")
    location_module = _module(study, "contactsLocationsModule")

    nct_id = identification.get("nctId")
    if not nct_id:
        return None

    lead_sponsor = sponsor_module.get("leadSponsor") or {}
    enrollment = design.get("enrollmentInfo") or {}
    conditions = sorted(
        {str(item).strip() for item in condition_module.get("conditions", []) if item and str(item).strip()},
        key=str.casefold,
    )
    interventions = []
    for intervention in intervention_module.get("interventions", []) or []:
        name = intervention.get("name")
        if name:
            interventions.append(
                {
                    "name": str(name).strip(),
                    "type": str(intervention.get("type") or "Not reported").strip(),
                }
            )
    interventions.sort(key=lambda item: (item["name"].casefold(), item["type"].casefold()))

    raw_locations = location_module.get("locations", []) or []
    countries = sorted(
        {
            str(location.get("country")).strip()
            for location in raw_locations
            if location.get("country") and str(location.get("country")).strip()
        },
        key=str.casefold,
    )

    search_text = json.dumps(study, ensure_ascii=False)
    imaging_signals = [label for label, pattern in IMAGING_TERMS if pattern.search(search_text)]

    phases = [
        str(phase).strip()
        for phase in design.get("phases", [])
        if phase and str(phase).strip().upper() not in {"NA", "N/A", "UNKNOWN", "NOT APPLICABLE"}
    ]
    last_update = status.get("lastUpdatePostDateStruct") or {}
    first_post = status.get("studyFirstPostDateStruct") or {}

    try:
        enrollment_count = int(enrollment.get("count")) if enrollment.get("count") is not None else None
    except (TypeError, ValueError):
        enrollment_count = None

    start_date = _date((status.get("startDateStruct") or {}).get("date"))
    completion_date = next(
        (
            parsed_date
            for parsed_date in (
                _date((status.get("completionDateStruct") or {}).get("date")),
                _date((status.get("primaryCompletionDateStruct") or {}).get("date")),
            )
            if parsed_date
        ),
        None,
    )
    duration_months: int | None = None
    if start_date and completion_date and completion_date >= start_date:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(completion_date)
        duration_months = (end.year - start.year) * 12 + end.month - start.month

    return {
        "nct_id": str(nct_id),
        "brief_title": str(identification.get("briefTitle") or "Untitled study").strip(),
        "study_type": str(design.get("studyType") or "Not reported").strip(),
        "overall_status": str(status.get("overallStatus") or "Not reported").strip(),
        "phase": ", ".join(phases) if phases else "Not applicable / not reported",
        "phases": phases,
        "sponsor_name": str(lead_sponsor.get("name") or "Not reported").strip(),
        "sponsor_class": str(lead_sponsor.get("class") or "Not reported").strip(),
        "enrollment_count": enrollment_count,
        "enrollment_type": str(enrollment.get("type") or "Not reported").strip(),
        "start_date": start_date,
        "completion_date": completion_date,
        "study_first_post_date": _date(first_post.get("date")),
        "last_update_date": _date(last_update.get("date")),
        "has_results": bool(study.get("hasResults", False)),
        "duration_months": duration_months,
        "conditions": conditions,
        "interventions": interventions,
        "countries": countries,
        "location_count": len(raw_locations),
        "is_imaging_related": bool(imaging_signals),
        "imaging_signals": imaging_signals,
    }


def dashboard_payload(
    studies: list[dict[str, Any]],
    *,
    generated_at: str,
    query_condition: str,
    api_total_count: int | None = None,
    page_count: int | None = None,
) -> dict[str, Any]:
    """Create the compact, public metadata snapshot consumed by the website."""

    rows = [row for study in studies if (row := extract_trial(study)) is not None]
    return {
        "metadata": {
            "source": "ClinicalTrials.gov API v2",
            "source_url": "https://clinicaltrials.gov/",
            "query": f"Condition: {query_condition}",
            "generated_at": generated_at,
            "study_count": len(rows),
            "api_total_count": api_total_count,
            "page_count": page_count,
            "scope_note": "Bounded public-record sample returned by the API query; public registry records are not patient-level data.",
        },
        "studies": rows,
    }
