{{ config(materialized='table') }}

select distinct
    md5(lower(btrim(phase))) as phase_key,
    phase
from {{ ref('stg_studies') }}
