{{ config(materialized='view') }}

select distinct
    latest.nct_id,
    nullif(btrim(condition.value), '') as condition_name
from {{ ref('int_latest_studies') }} as latest
cross join lateral jsonb_array_elements_text(
    coalesce(latest.source_payload #> '{protocolSection,conditionsModule,conditions}', '[]'::jsonb)
) as condition(value)
where nullif(btrim(condition.value), '') is not null
