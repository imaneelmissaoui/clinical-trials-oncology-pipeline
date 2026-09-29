{{ config(materialized='view') }}

select distinct
    latest.nct_id,
    nullif(btrim(location.value ->> 'country'), '') as country_name,
    nullif(btrim(location.value ->> 'city'), '') as city_name,
    nullif(btrim(location.value ->> 'facility'), '') as facility_name
from {{ ref('int_latest_studies') }} as latest
cross join lateral jsonb_array_elements(
    coalesce(latest.source_payload #> '{protocolSection,contactsLocationsModule,locations}', '[]'::jsonb)
) as location(value)
where nullif(btrim(location.value ->> 'country'), '') is not null
   or nullif(btrim(location.value ->> 'city'), '') is not null
   or nullif(btrim(location.value ->> 'facility'), '') is not null
