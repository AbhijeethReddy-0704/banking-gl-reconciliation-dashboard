# Multi-stage Dockerfile for banking GL reconciliation dashboard

FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/raw data/processed

# Production stage
FROM base as production

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://postgres:password@postgres:5432/banking_db

EXPOSE 8000 8501

CMD ["python", "-m", "pipelines.etl_main"]
