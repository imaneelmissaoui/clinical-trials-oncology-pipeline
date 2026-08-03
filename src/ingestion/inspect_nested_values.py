from pathlib import Path
import json
from typing import Any


INPUT_PATH = Path("data/raw/lymphoma_studies_sample.json")


def print_json_section(title: str, value: Any) -> None:
    """Print a Python value as formatted JSON."""

    print()
    print(title)
    print("=" * 80)

    print(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        )
    )


def main() -> None:
    """Inspect important nested values from the first clinical trial."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Run explore_api.py first."
        )

    payload = json.loads(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    studies = payload.get("studies", [])

    if not studies:
        print("No studies were found.")
        return

    first_study = studies[0]

    protocol_section = first_study.get(
        "protocolSection",
        {},
    )

    identification = protocol_section.get(
        "identificationModule",
        {},
    )

    status = protocol_section.get(
        "statusModule",
        {},
    )

    sponsors = protocol_section.get(
        "sponsorCollaboratorsModule",
        {},
    )

    conditions = protocol_section.get(
        "conditionsModule",
        {},
    )

    design = protocol_section.get(
        "designModule",
        {},
    )

    arms_interventions = protocol_section.get(
        "armsInterventionsModule",
        {},
    )

    contacts_locations = protocol_section.get(
        "contactsLocationsModule",
        {},
    )

    print(f"NCT ID: {identification.get('nctId')}")
    print(f"Title: {identification.get('briefTitle')}")

    print_json_section(
        "STATUS DATES",
        {
            "statusVerifiedDate": status.get("statusVerifiedDate"),
            "overallStatus": status.get("overallStatus"),
            "startDateStruct": status.get("startDateStruct"),
            "primaryCompletionDateStruct": status.get(
                "primaryCompletionDateStruct"
            ),
            "completionDateStruct": status.get(
                "completionDateStruct"
            ),
            "lastUpdatePostDateStruct": status.get(
                "lastUpdatePostDateStruct"
            ),
        },
    )

    print_json_section(
        "LEAD SPONSOR",
        sponsors.get("leadSponsor"),
    )

    collaborators = sponsors.get("collaborators", [])

    print_json_section(
        "FIRST COLLABORATOR",
        collaborators[0] if collaborators else None,
    )

    print_json_section(
        "CONDITIONS AND KEYWORDS",
        {
            "conditions": conditions.get("conditions", []),
            "keywords": conditions.get("keywords", []),
        },
    )

    print_json_section(
        "STUDY DESIGN",
        design,
    )

    interventions = arms_interventions.get(
        "interventions",
        [],
    )

    print_json_section(
        "FIRST INTERVENTION",
        interventions[0] if interventions else None,
    )

    locations = contacts_locations.get(
        "locations",
        [],
    )

    print_json_section(
        "FIRST LOCATION",
        locations[0] if locations else None,
    )


if __name__ == "__main__":
    main()