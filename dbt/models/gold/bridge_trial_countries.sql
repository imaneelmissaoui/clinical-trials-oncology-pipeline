{{ config(materialized='table') }}

select
    locations.nct_id,
    countries.country_key,
    locations.country_name,
    count(*) as location_count
from {{ ref('stg_locations') }} as locations
join {{ ref('dim_countries') }} as countries using (country_name)
group by locations.nct_id, countries.country_key, locations.country_name
