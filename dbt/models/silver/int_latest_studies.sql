{{ config(materialized='view') }}

with latest_run as (
    select ingestion_run_id
    from {{ source('bronze', 'ingestion_runs') }}
    order by completed_at desc, started_at desc, ingestion_run_id desc
    limit 1
), ranked_records as (
    select
        nct_id,
        source_payload,
        extracted_at,
        source_updated_at,
        ingestion_run_id,
        api_query,
        row_number() over (
            partition by nct_id
            order by extracted_at desc, source_updated_at desc nulls last, record_id desc
        ) as record_rank
    from {{ source('bronze', 'raw_studies') }} as raw_studies
    join latest_run using (ingestion_run_id)
)

select
    nct_id,
    source_payload,
    extracted_at,
    source_updated_at,
    ingestion_run_id,
    api_query
from ranked_records
where record_rank = 1
