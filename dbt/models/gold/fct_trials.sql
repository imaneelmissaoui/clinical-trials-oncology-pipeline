{{ config(materialized='table') }}

with condition_counts as (
    select nct_id, count(*) as condition_count
    from {{ ref('stg_conditions') }}
    group by nct_id
), intervention_counts as (
    select nct_id, count(*) as intervention_count
    from {{ ref('stg_interventions') }}
    group by nct_id
), location_counts as (
    select
        nct_id,
        count(*) as location_count,
        count(distinct country_name) as country_count
    from {{ ref('stg_locations') }}
    group by nct_id
)

select
    study.nct_id,
    status.status_key,
    phase.phase_key,
    study_type.study_type_key,
    sponsor.sponsor_key,
    study.brief_title,
    study.official_title,
    study.overall_status,
    study.phase,
    study.study_type,
    study.sponsor_name,
    study.sponsor_class,
    study.enrollment_count,
    study.enrollment_type,
    study.start_date,
    study.completion_date,
    study.study_first_post_date,
    study.last_update_date,
    study.has_results,
    study.duration_months,
    coalesce(condition_counts.condition_count, 0) as condition_count,
    coalesce(intervention_counts.intervention_count, 0) as intervention_count,
    coalesce(location_counts.location_count, 0) as location_count,
    coalesce(location_counts.country_count, 0) as country_count,
    study.is_imaging_related,
    study.imaging_signals,
    study.api_query,
    study.ingestion_run_id
from {{ ref('stg_studies') }} as study
join {{ ref('dim_study_status') }} as status using (overall_status)
join {{ ref('dim_study_phase') }} as phase using (phase)
join {{ ref('dim_study_type') }} as study_type using (study_type)
join {{ ref('dim_sponsors') }} as sponsor using (sponsor_name, sponsor_class)
left join condition_counts using (nct_id)
left join intervention_counts using (nct_id)
left join location_counts using (nct_id)
