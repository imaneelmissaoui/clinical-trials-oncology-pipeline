from clinical_trials_pipeline.transform import dashboard_payload, extract_trial


def sample_study():
    return {
        "hasResults": True,
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT00000001",
                "briefTitle": "PET/CT guided lymphoma study",
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "startDateStruct": {"date": "2024-03"},
                "completionDateStruct": {"date": "2026"},
                "studyFirstPostDateStruct": {"date": "2024-02-17"},
                "lastUpdatePostDateStruct": {"date": "2025-11-04"},
            },
            "sponsorCollaboratorsModule": {
                "leadSponsor": {"name": "Example Institute", "class": "OTHER"}
            },
            "conditionsModule": {"conditions": ["Lymphoma", "Hodgkin Disease"]},
            "designModule": {
                "studyType": "INTERVENTIONAL",
                "phases": ["PHASE2"],
                "enrollmentInfo": {"count": 42, "type": "ESTIMATED"},
            },
            "armsInterventionsModule": {
                "interventions": [{"name": "Immunotherapy", "type": "DRUG"}]
            },
            "contactsLocationsModule": {
                "locations": [
                    {"country": "France", "city": "Paris"},
                    {"country": "France", "city": "Lyon"},
                ]
            },
        },
    }


def test_extract_trial_flattens_nested_fields_and_normalizes_partial_dates():
    trial = extract_trial(sample_study())

    assert trial["nct_id"] == "NCT00000001"
    assert trial["phase"] == "PHASE2"
    assert trial["start_date"] == "2024-03-01"
    assert trial["completion_date"] == "2026-01-01"
    assert trial["enrollment_count"] == 42
    assert trial["countries"] == ["France"]
    assert trial["location_count"] == 2
    assert trial["is_imaging_related"] is True
    assert trial["imaging_signals"] == ["PET / PET-CT"]
    assert trial["has_results"] is True


def test_missing_nct_id_is_not_exported():
    assert extract_trial({"protocolSection": {}}) is None


def test_non_applicable_phase_placeholder_is_standardized():
    study = sample_study()
    study["protocolSection"]["designModule"]["phases"] = ["NA"]

    trial = extract_trial(study)

    assert trial["phase"] == "Not applicable / not reported"
    assert trial["phases"] == []


def test_invalid_partial_and_complete_dates_are_null():
    study = sample_study()
    status = study["protocolSection"]["statusModule"]
    status["startDateStruct"]["date"] = "2024-13"
    status["completionDateStruct"]["date"] = "2026-02-30"
    status["studyFirstPostDateStruct"]["date"] = "2024-00-01"

    trial = extract_trial(study)

    assert trial["start_date"] is None
    assert trial["completion_date"] is None
    assert trial["study_first_post_date"] is None
    assert trial["duration_months"] is None


def test_dashboard_payload_has_source_provenance_and_only_valid_trials():
    payload = dashboard_payload(
        [sample_study(), {"protocolSection": {}}],
        generated_at="2026-09-29T09:00:00+00:00",
        query_condition="lymphoma",
        api_total_count=11291,
        page_count=1,
    )

    assert payload["metadata"]["study_count"] == 1
    assert payload["metadata"]["api_total_count"] == 11291
    assert payload["metadata"]["source"] == "ClinicalTrials.gov API v2"
    assert len(payload["studies"]) == 1
