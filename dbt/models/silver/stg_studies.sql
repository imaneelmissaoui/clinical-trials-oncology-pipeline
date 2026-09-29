{{ config(materialized='view') }}

with source_records as (
    select
        nct_id,
        source_payload,
        extracted_at,
        source_updated_at,
        ingestion_run_id,
        api_query,
        source_payload #>> '{protocolSection,identificationModule,briefTitle}' as brief_title,
        source_payload #>> '{protocolSection,identificationModule,officialTitle}' as official_title,
        source_payload #>> '{protocolSection,statusModule,overallStatus}' as overall_status,
        source_payload #>> '{protocolSection,designModule,studyType}' as study_type,
        source_payload #>> '{protocolSection,sponsorCollaboratorsModule,leadSponsor,name}' as sponsor_name,
        source_payload #>> '{protocolSection,sponsorCollaboratorsModule,leadSponsor,class}' as sponsor_class,
        source_payload #>> '{protocolSection,designModule,enrollmentInfo,count}' as enrollment_count_text,
        source_payload #>> '{protocolSection,designModule,enrollmentInfo,type}' as enrollment_type,
        source_payload #>> '{protocolSection,statusModule,startDateStruct,date}' as start_date_text,
        coalesce(
            nullif(source_payload #>> '{protocolSection,statusModule,completionDateStruct,date}', 'NA'),
            nullif(source_payload #>> '{protocolSection,statusModule,primaryCompletionDateStruct,date}', 'NA')
        ) as completion_date_text,
        source_payload #>> '{protocolSection,statusModule,studyFirstPostDateStruct,date}' as first_post_date_text,
        coalesce(
            source_payload #>> '{protocolSection,statusModule,lastUpdatePostDateStruct,date}',
            source_updated_at
        ) as last_update_date_text,
        coalesce(source_payload ->> 'hasResults', 'false')::boolean as has_results,
        coalesce(source_payload #> '{protocolSection,designModule,phases}', '[]'::jsonb) as phases_json,
        coalesce(source_payload #> '{protocolSection,conditionsModule,conditions}', '[]'::jsonb) as conditions_json,
        coalesce(source_payload #> '{protocolSection,armsInterventionsModule,interventions}', '[]'::jsonb) as interventions_json,
        coalesce(source_payload #> '{protocolSection,contactsLocationsModule,locations}', '[]'::jsonb) as locations_json
    from {{ ref('int_latest_studies') }}
), parsed as (
    select
        *,
        {{ parse_partial_date('start_date_text') }} as start_date,
        {{ parse_partial_date('completion_date_text') }} as completion_date,
        {{ parse_partial_date('first_post_date_text') }} as study_first_post_date,
        {{ parse_partial_date('last_update_date_text') }} as last_update_date,
        case
            when enrollment_count_text ~ '^[0-9]+$' then enrollment_count_text::integer
            else null
        end as enrollment_count,
        (
            select string_agg(value, ', ' order by value)
            from jsonb_array_elements_text(phases_json) as phase_items(value)
            where upper(btrim(value)) not in ('NA', 'N/A', 'UNKNOWN', 'NOT APPLICABLE')
        ) as phase
    from source_records
)

select
    nct_id,
    coalesce(nullif(btrim(brief_title), ''), 'Untitled study') as brief_title,
    nullif(btrim(official_title), '') as official_title,
    coalesce(nullif(btrim(overall_status), ''), 'Not reported') as overall_status,
    coalesce(nullif(btrim(study_type), ''), 'Not reported') as study_type,
    coalesce(nullif(btrim(sponsor_name), ''), 'Not reported') as sponsor_name,
    coalesce(nullif(btrim(sponsor_class), ''), 'Not reported') as sponsor_class,
    case
        when upper(btrim(coalesce(phase, ''))) in ('NA', 'N/A', 'UNKNOWN', 'NOT APPLICABLE')
            then 'Not applicable / not reported'
        else coalesce(nullif(btrim(phase), ''), 'Not applicable / not reported')
    end as phase,
    enrollment_count,
    coalesce(nullif(btrim(enrollment_type), ''), 'Not reported') as enrollment_type,
    start_date,
    completion_date,
    study_first_post_date,
    last_update_date,
    has_results,
    case
        when start_date is not null and completion_date >= start_date
        then ((extract(year from completion_date) - extract(year from start_date)) * 12
              + extract(month from completion_date) - extract(month from start_date))::integer
        else null
    end as duration_months,
    source_updated_at,
    extracted_at,
    ingestion_run_id,
    api_query,
    source_payload::text ~* '(pet([[:space:]]*/[[:space:]]*ct|[- ]?ct)?|mri|magnetic resonance imaging|ct scan|computed tomography|imaging|radiology|radiologic|ultrasound|sonography)' as is_imaging_related,
    array_remove(array[
        case when source_payload::text ~* '(pet([[:space:]]*/[[:space:]]*ct|[- ]?ct)?)' then 'PET / PET-CT' end,
        case when source_payload::text ~* '(mri|magnetic resonance imaging)' then 'MRI' end,
        case when source_payload::text ~* '(ct scan|computed tomography)' then 'CT' end,
        case when source_payload::text ~* '(imaging|radiology|radiologic)' then 'Imaging' end,
        case when source_payload::text ~* '(ultrasound|sonography)' then 'Ultrasound' end
    ], null) as imaging_signals
from parsed
