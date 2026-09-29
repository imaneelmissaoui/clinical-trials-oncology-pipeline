{{ config(materialized='table') }}

select distinct
    md5(lower(btrim(sponsor_name)) || '|' || lower(btrim(sponsor_class))) as sponsor_key,
    sponsor_name,
    sponsor_class
from {{ ref('stg_studies') }}
