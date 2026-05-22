.PHONY: help install generate-data run-pipeline validate test api dashboard lint format check-types clean docker-build docker-up docker-down

help:
	@echo "Banking GL Reconciliation Dashboard"
	@echo "Available commands:"
	@echo "  make install           Install dependencies"
	@echo "  make generate-data     Generate synthetic data"
	@echo "  make run-pipeline      Run ETL pipeline"
	@echo "  make validate          Validate data quality"
	@echo "  make test              Run tests"
	@echo "  make api               Start FastAPI server"
	@echo "  make dashboard         Start Streamlit dashboard"
	@echo "  make lint              Run code linter"
	@echo "  make format            Format code"
	@echo "  make check-types       Run type checker"
	@echo "  make docker-build      Build Docker images"
	@echo "  make docker-up         Start Docker Compose"
	@echo "  make docker-down       Stop Docker Compose"
	@echo "  make clean             Clean generated files"

install:
	pip install -r requirements.txt

generate-data:
	python -m pipelines.generate_synthetic_data

run-pipeline:
	python -m pipelines.etl_main

validate:
	python -m pipelines.data_validation

test:
	pytest -v --cov=app --cov=pipelines tests/

api:
	uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	streamlit run streamlit_app.py

lint:
	ruff check app/ pipelines/ tests/

format:
	ruff format app/ pipelines/ tests/
	black app/ pipelines/ tests/

check-types:
	mypy app/ pipelines/ --ignore-missing-imports

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage
	rm -rf data/raw/*.csv data/raw/*.parquet
	rm -rf data/processed/*.parquet

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

db-init:
	python -m pipelines.init_database

db-reset:
	python -m pipelines.init_database --reset
