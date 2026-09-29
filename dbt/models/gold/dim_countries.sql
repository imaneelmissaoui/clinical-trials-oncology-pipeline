{{ config(materialized='table') }}

select distinct
    md5(lower(btrim(country_name))) as country_key,
    country_name
from {{ ref('stg_locations') }}
where country_name is not null
