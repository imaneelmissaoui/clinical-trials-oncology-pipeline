{{ config(materialized='view') }}

select distinct
    latest.nct_id,
    nullif(btrim(intervention.value ->> 'name'), '') as intervention_name,
    coalesce(nullif(btrim(intervention.value ->> 'type'), ''), 'Not reported') as intervention_type
from {{ ref('int_latest_studies') }} as latest
cross join lateral jsonb_array_elements(
    coalesce(latest.source_payload #> '{protocolSection,armsInterventionsModule,interventions}', '[]'::jsonb)
) as intervention(value)
where nullif(btrim(intervention.value ->> 'name'), '') is not null
