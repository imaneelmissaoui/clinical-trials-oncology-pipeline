# Data dictionary

| Field | Layer/model | Meaning and handling |
|---|---|---|
| `nct_id` | Bronze, Silver and Gold | ClinicalTrials.gov identifier; Silver and `gold.fct_trials` are unique at this grain. |
| `source_payload` | `bronze.raw_studies` | Full public source record stored as JSONB. |
| `extracted_at` | `bronze.raw_studies` | Database insertion time for the snapshot. |
| `source_updated_at` / `last_update_date` | Bronze / Silver and Gold | Registry-posted record update date. It is not the extraction time. |
| `ingestion_run_id` | Bronze, Silver, Gold and `bronze.ingestion_runs` | UTC run identifier used to trace snapshots. |
| `api_query` | Bronze, Silver and Gold | Condition query used for the API request. |
| `query_condition` | `bronze.ingestion_runs` | Condition query submitted to ClinicalTrials.gov. |
| `api_total_count` | `bronze.ingestion_runs` | API-reported matches at retrieval time; can exceed the bounded sample stored by that run. |
| `page_count` | `bronze.ingestion_runs` | Number of API pages fetched for that run. |
| `fetched_count`, `inserted_count`, `skipped_count` | `bronze.ingestion_runs` | Run-level record counts for extraction and Bronze loading. |
| `overall_status` | Silver and Gold | Current status reported by the registry. |
| `phase` | Silver and Gold | Phase values grouped into a displayable label; non-applicable placeholders are standardized. |
| `study_type` | Silver and Gold | Registry study type, such as interventional or observational. |
| `sponsor_name`, `sponsor_class` | Silver and Gold | Lead sponsor name and registry sponsor classification. |
| `enrollment_count`, `enrollment_type` | Silver and Gold | Enrollment estimate or actual count and its source type. |
| `start_date`, `completion_date` | Silver and Gold | Standardized source dates; partial values use the first day of their source period. Completion falls back to primary completion when needed. |
| `duration_months` | Silver and Gold | Calendar-month difference when start and completion dates are valid and ordered. |
| `has_results` | Silver and Gold | Registry flag indicating posted results are available. |
| `is_imaging_related`, `imaging_signals` | Silver and Gold | Keyword screening from the full public record text; exploratory signal only. |
| `condition_count` | Gold fact | Number of distinct registered conditions on the study. |
| `intervention_count` | Gold fact | Number of distinct registered interventions on the study. |
| `location_count` | Gold fact | Number of distinct location records with at least one reported country, city or facility. |
| `country_count` | Gold fact | Number of distinct registered countries. |

## Grain of multi-valued models

- `silver.stg_conditions`: one row per `(nct_id, condition_name)`.
- `silver.stg_interventions`: one row per `(nct_id, intervention_name, intervention_type)`.
- `silver.stg_locations`: one row per study, country, city and facility combination.
- Gold bridge tables keep the same relationship grain, with `bridge_trial_countries` adding the count of registered locations per country.
