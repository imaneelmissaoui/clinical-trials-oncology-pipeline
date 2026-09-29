select nct_id
from {{ ref('fct_trials') }}
where condition_count < 0
   or intervention_count < 0
   or location_count < 0
   or country_count < 0
   or (duration_months is not null and duration_months < 0)
