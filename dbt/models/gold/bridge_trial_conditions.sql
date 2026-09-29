{{ config(materialized='table') }}

select distinct nct_id, condition_name
from {{ ref('stg_conditions') }}
