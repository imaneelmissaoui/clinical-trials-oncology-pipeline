from pathlib import Path
import json
from typing import Any


INPUT_PATH = Path("data/raw/lymphoma_studies_sample.json")


def describe_value(name: str, value: Any) -> None:
    """Print the Python type and a short description of a value."""

    value_type = type(value).__name__

    if isinstance(value, dict):
        print(f"{name}: {value_type} containing {len(value)} keys")

    elif isinstance(value, list):
        print(f"{name}: {value_type} containing {len(value)} items")

    else:
        print(f"{name}: {value_type} = {value}")


# هادي هي الـfunction الجديدة
def print_module_fields(
    module_name: str,
    module_data: dict[str, Any],
) -> None:
    """Print all top-level fields available inside a study module."""

    print()
    print(module_name.upper())
    print("=" * 80)

    if not module_data:
        print("Module not available for this study.")
        return

    for field_name, field_value in module_data.items():
        describe_value(field_name, field_value)


def main() -> None:
    """Inspect the structure of the saved ClinicalTrials.gov response."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Run explore_api.py first."
        )

    raw_text = INPUT_PATH.read_text(encoding="utf-8")
    payload = json.loads(raw_text)

    print("TOP-LEVEL RESPONSE")
    print("=" * 80)

    for key, value in payload.items():
        describe_value(key, value)

    studies = payload.get("studies", [])

    if not studies:
        print("No studies were found.")
        return

    first_study = studies[0]

    print()
    print("FIRST STUDY")
    print("=" * 80)

    for key, value in first_study.items():
        describe_value(key, value)

    protocol_section = first_study.get("protocolSection", {})

    print()
    print("PROTOCOL SECTION MODULES")
    print("=" * 80)

    for module_name, module_value in protocol_section.items():
        describe_value(module_name, module_value)

    identification_module = protocol_section.get(
        "identificationModule",
        {},
    )

    print()
    print("IDENTIFICATION MODULE")
    print("=" * 80)

    for field_name, field_value in identification_module.items():
        describe_value(field_name, field_value)

    selected_modules = [
        "statusModule",
        "sponsorCollaboratorsModule",
        "conditionsModule",
        "designModule",
        "armsInterventionsModule",
        "contactsLocationsModule",
    ]

    for module_name in selected_modules:
        module_data = protocol_section.get(module_name, {})

        print_module_fields(
            module_name=module_name,
            module_data=module_data,
        )


if __name__ == "__main__":
    main()