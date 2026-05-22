"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.api.main import app


client = TestClient(app)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_monthly_kpis():
    """Test monthly KPIs endpoint."""
    response = client.get("/kpis/monthly")
    assert response.status_code == 200
    data = response.json()
    assert "monthly_kpis" in data
    assert "ytd_revenue" in data
    assert "ytd_transactions" in data


def test_product_line_kpis():
    """Test product line KPIs endpoint."""
    response = client.get("/kpis/product-line")
    assert response.status_code == 200
    data = response.json()
    assert "product_lines" in data
    assert "total_revenue" in data


def test_reconciliation_summary():
    """Test reconciliation summary endpoint."""
    response = client.get("/reconciliation/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert "matched" in data
    assert "match_rate" in data


def test_exceptions_list():
    """Test exceptions endpoint."""
    response = client.get("/reconciliation/exceptions")
    assert response.status_code == 200
    data = response.json()
    assert "exceptions" in data
    assert "total_count" in data


def test_data_quality_summary():
    """Test data quality endpoint."""
    response = client.get("/data-quality/summary")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "overall_status" in data


def test_pipeline_latest_run():
    """Test pipeline latest run endpoint."""
    response = client.get("/pipeline/latest-run")
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "status" in data
