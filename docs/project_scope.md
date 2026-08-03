# Oncology Clinical Trials Intelligence Pipeline

## Project Overview

This project builds an end-to-end data engineering pipeline for collecting, storing, transforming, testing, and visualizing public oncology clinical trial data.

The first version of the pipeline will focus on lymphoma and medical imaging-related clinical trials retrieved from the ClinicalTrials.gov API v2.

## Project Objectives

The pipeline will:

1. Extract clinical trial records from the ClinicalTrials.gov API.
2. Preserve the original source data in a raw Bronze layer.
3. Clean and standardize the data in a Silver layer.
4. Build analytics-ready datasets in a Gold layer.
5. Validate data quality using automated tests.
6. Visualize clinical trial trends using a business intelligence dashboard.
7. Support repeatable and incremental pipeline executions.

## Initial Analytical Questions

The final datasets should help answer questions such as:

* How many lymphoma trials are currently recruiting?
* How are clinical trials distributed by phase?
* Which countries host the most active trials?
* Which organizations sponsor the most oncology trials?
* What intervention types are most frequently studied?
* How long do oncology clinical trials typically last?
* Which trial records have not been updated recently?
* How frequently are PET, PET/CT, MRI, and other imaging technologies used in oncology trials?

## Initial Data Source

ClinicalTrials.gov API v2.

The first pipeline version will retrieve a limited and reproducible subset of lymphoma and medical imaging-related clinical trials.

## Planned Technology Stack

* Python for data extraction and pipeline logic
* PostgreSQL for data storage
* dbt for SQL transformations, testing, and documentation
* Docker and Docker Compose for reproducible environments
* Metabase for dashboarding
* Git and GitHub for version control
* GitHub Actions for continuous integration

## Planned Architecture

ClinicalTrials.gov API
→ Python ingestion
→ PostgreSQL Bronze layer
→ dbt Silver layer
→ dbt Gold layer
→ Metabase dashboard

## Future Improvements

Potential future versions may include:

* Incremental ingestion of newly created or updated trials
* Airflow orchestration
* Integration with an additional healthcare data source
* Cloud deployment
* Automated data freshness monitoring
* More advanced data quality checks
