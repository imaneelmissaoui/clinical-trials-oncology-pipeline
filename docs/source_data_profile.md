# ClinicalTrials.gov source profile

## Endpoint and query

- Endpoint: `GET https://clinicaltrials.gov/api/v2/studies`
- Default query: `query.cond=lymphoma`
- Response: JSON study records containing a nested `protocolSection`, optional `derivedSection`, and a `hasResults` flag.
- Pagination: `pageSize` with a `nextPageToken` supplied as `pageToken` on the following request.
- Project defaults: page size 250; maximum 1,000 unique studies per run.

The API response `totalCount` describes the number of query matches at request time, while a bounded run may store only the first configured maximum. The portfolio JSON includes both values when the API returns a total. Registry content changes over time, so the count in a refreshed dashboard may differ.

## Nested fields used

| Study module | API values used | Silver/Gold attributes |
|---|---|---|
| `identificationModule` | `nctId`, `briefTitle`, `officialTitle` | NCT ID and study titles |
| `statusModule` | `overallStatus`, `startDateStruct.date`, `completionDateStruct.date`, `primaryCompletionDateStruct.date`, `studyFirstPostDateStruct.date`, `lastUpdatePostDateStruct.date` | Status, normalized dates and duration |
| `sponsorCollaboratorsModule` | `leadSponsor.name`, `leadSponsor.class` | Sponsor dimension |
| `conditionsModule` | `conditions[]` | Study-condition bridge |
| `designModule` | `studyType`, `phases[]`, `enrollmentInfo.count`, `enrollmentInfo.type` | Study type, phase, enrollment |
| `armsInterventionsModule` | `interventions[].name`, `interventions[].type` | Study-intervention bridge |
| `contactsLocationsModule` | `locations[].country`, `locations[].city`, `locations[].facility` | Study-country bridge and location count |
| Top level | `hasResults` | Results availability flag |

The complete study object is stored in Bronze as JSONB. Contact details remain in the raw registry payload for traceability but are not selected into Silver, Gold or the static dashboard.

Run-level provenance is stored separately in `bronze.ingestion_runs`: start/completion timestamps, query condition, API `totalCount`, page count and fetched/inserted/skipped row counts.

## Data handling rules

- NCT ID is the natural identifier for a study; one Bronze row is retained per NCT ID and ingestion run.
- A partial source date `YYYY` is interpreted as January 1 of that year; `YYYY-MM` as the first day of that month. The normalized date is an analysis convention and not a more precise source date.
- Blank or unavailable values remain null or are labeled `Not reported` for dashboard display.
- `NA`, `N/A`, `UNKNOWN` and `NOT APPLICABLE` phase values map to `Not applicable / not reported`.
- Repeated conditions, interventions and locations are expanded into separate Silver rows and Gold bridge tables.
- The dashboard exports only study metadata used for exploration; it does not export central-contact fields or patient-level information.

## Snapshot note

The committed portfolio dashboard is a dated 1,000-study preview captured from the public API. The API reported 11,291 matches when that snapshot was collected on 29 September 2026. This is retrieval metadata, not a stable registry total. Run the complete pipeline to refresh Bronze and export a current dashboard from Gold.
