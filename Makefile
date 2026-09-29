.PHONY: setup up down run preview test dbt-build dashboard

setup:
	python -m pip install -e ".[dev]"

up:
	docker compose up -d --wait postgres metabase

down:
	docker compose down

run:
	python -m clinical_trials_pipeline run

preview:
	python -m clinical_trials_pipeline preview --output ../imaneelmissaoui.github.io/projects/clinical-trials-oncology-pipeline/data/dashboard.json

test:
	pytest

dbt-build:
	cd dbt && dbt build --profiles-dir .

dashboard:
	python -m clinical_trials_pipeline export-dashboard --output ../imaneelmissaoui.github.io/projects/clinical-trials-oncology-pipeline/data/dashboard.json
