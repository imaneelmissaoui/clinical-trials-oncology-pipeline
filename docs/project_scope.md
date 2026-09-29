# Project scope and analytical definitions

## Objective

Build a reproducible data pipeline around public ClinicalTrials.gov study records, with lymphoma as the default condition query. Preserve each source record, produce normalized analytical tables, validate their grain and relationships, and make the resulting study landscape explorable.

## In scope

- ClinicalTrials.gov API v2 study search and cursor pagination.
- A bounded run of up to 1,000 unique studies by default; the cap and page size are configurable.
- Append-only Bronze snapshots with source payload, run ID, extraction timestamp, query and registry update date.
- dbt Silver normalization for studies, conditions, interventions and study locations.
- A Gold one-row-per-study fact table, dimensions and bridges for repeated values.
- Automated source-independent Python tests and dbt data-quality tests.
- Metabase access to the Gold warehouse and a static, interactive dashboard snapshot for the portfolio.

## Analytical definitions

| Indicator | Definition |
|---|---|
| Study count | Distinct NCT IDs in the selected snapshot; never a count of sites or interventions. |
| Recruiting | `overallStatus = RECRUITING` in the current registry record. |
| Country count | Distinct country labels among the locations attached to visible studies. |
| Location count | Distinct study-location records with at least one reported country, city or facility retained in Silver. |
| Study duration | Difference in calendar months between reported start and completion dates when both can be parsed and completion is not before start. |
| Imaging-related | Text keyword screening for PET/PET-CT, MRI, CT, imaging/radiology and ultrasound terms. It does not establish trial purpose or measure imaging use. |
| Has results | The source record's `hasResults` flag; it does not assess result quality or findings. |

## Out of scope

- Patient-level data, eligibility matching or clinical recommendations.
- Statistical evaluation of treatment effects or posted study results.
- Automatic scheduling, change-data capture between API snapshots, Airflow and cloud hosting.
- A claim that the bounded sample is a census of all lymphoma studies.

## Refresh behavior

Each manual run follows the API page token until it reaches the configured study cap or the API has no next-page token. It appends each captured NCT ID to Bronze under a new run ID. Silver first chooses the newest completed ingestion run, then selects one captured row per NCT ID from that run. Historical payloads remain in Bronze. A future scheduled incremental design could track changed records between runs; this version does not claim to do so.
