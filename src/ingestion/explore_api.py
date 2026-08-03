from pathlib import Path
import json

import requests


API_URL = "https://clinicaltrials.gov/api/v2/studies"

PARAMS = {
    "query.cond": "lymphoma",
    "pageSize": 5,
    "format": "json",
}


def main() -> None:
    """Retrieve and inspect a small sample of lymphoma clinical trials."""

    print("Sending request to ClinicalTrials.gov...")

    response = requests.get(
        API_URL,
        params=PARAMS,
        timeout=30,
    )

    print(f"Requested URL: {response.url}")
    print(f"HTTP status code: {response.status_code}")

    response.raise_for_status()

    payload = response.json()
    studies = payload.get("studies", [])

    print(f"Number of studies received: {len(studies)}")
    print()

    for position, study in enumerate(studies, start=1):
        protocol_section = study.get("protocolSection", {})

        identification = protocol_section.get(
            "identificationModule",
            {},
        )

        status_module = protocol_section.get(
            "statusModule",
            {},
        )

        nct_id = identification.get("nctId")
        title = identification.get("briefTitle")
        status = status_module.get("overallStatus")

        print(f"Study {position}")
        print(f"NCT ID: {nct_id}")
        print(f"Title: {title}")
        print(f"Status: {status}")
        print("-" * 80)

    output_path = Path(
        "data/raw/lymphoma_studies_sample.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(f"Raw JSON saved to: {output_path}")


if __name__ == "__main__":
    main()