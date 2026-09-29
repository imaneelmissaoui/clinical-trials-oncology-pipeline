{{ config(materialized='table') }}

select distinct
    md5(lower(btrim(overall_status))) as status_key,
    overall_status
from {{ ref('stg_studies') }}
