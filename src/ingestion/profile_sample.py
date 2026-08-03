from pathlib import Path
import json


INPUT_PATH = Path("data/raw/lymphoma_studies_sample.json")


def main() -> None:
    """Compare the structure and main values of all sample studies."""

    payload = json.loads(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    studies = payload.get("studies", [])

    for position, study in enumerate(studies, start=1):
        protocol = study.get("protocolSection", {})

        identification = protocol.get(
            "identificationModule",
            {},
        )

        status = protocol.get(
            "statusModule",
            {},
        )

        sponsors = protocol.get(
            "sponsorCollaboratorsModule",
            {},
        )

        conditions = protocol.get(
            "conditionsModule",
            {},
        )

        design = protocol.get(
            "designModule",
            {},
        )

        interventions_module = protocol.get(
            "armsInterventionsModule",
            {},
        )

        locations_module = protocol.get(
            "contactsLocationsModule",
            {},
        )

        print()
        print(f"STUDY {position}")
        print("=" * 80)

        print(f"NCT ID: {identification.get('nctId')}")
        print(f"Status: {status.get('overallStatus')}")
        print(f"Start date: {status.get('startDateStruct')}")
        print(f"Phases: {design.get('phases', [])}")
        print(f"Study type: {design.get('studyType')}")

        print(
            "Lead sponsor:",
            sponsors.get("leadSponsor"),
        )

        print(
            "Number of collaborators:",
            len(sponsors.get("collaborators", [])),
        )

        print(
            "Number of conditions:",
            len(conditions.get("conditions", [])),
        )

        print(
            "Number of keywords:",
            len(conditions.get("keywords", [])),
        )

        print(
            "Number of interventions:",
            len(
                interventions_module.get(
                    "interventions",
                    [],
                )
            ),
        )

        print(
            "Number of locations:",
            len(
                locations_module.get(
                    "locations",
                    [],
                )
            ),
        )

        print(f"Has results: {study.get('hasResults')}")


if __name__ == "__main__":
    main()