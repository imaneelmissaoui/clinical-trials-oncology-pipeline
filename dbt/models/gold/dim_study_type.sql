{{ config(materialized='table') }}

select distinct
    md5(lower(btrim(study_type))) as study_type_key,
    study_type
from {{ ref('stg_studies') }}
