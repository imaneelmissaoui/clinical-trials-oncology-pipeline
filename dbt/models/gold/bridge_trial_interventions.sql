{{ config(materialized='table') }}

select distinct nct_id, intervention_name, intervention_type
from {{ ref('stg_interventions') }}
