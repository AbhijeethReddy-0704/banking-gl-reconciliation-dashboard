"""Tests for synthetic data generation."""

import pytest
import pandas as pd
from pathlib import Path
from pipelines.generate_synthetic_data import (
    generate_customers, generate_branches, generate_employees,
    generate_product_lines, generate_accounts, generate_transactions,
    generate_gl_entries, generate_calendar
)


def cleanup_csv(filename: str):
    """Clean up generated CSV file."""
    path = Path(f"data/raw/{filename}.csv")
    if path.exists():
        path.unlink()


def test_generate_customers():
    """Test customer generation."""
    df = generate_customers(100)
    cleanup_csv("customers")

    assert len(df) == 100
    assert "customer_id" in df.columns
    assert "customer_name" in df.columns
    assert "risk_segment" in df.columns
    assert df["customer_id"].is_unique


def test_generate_branches():
    """Test branch generation."""
    df = generate_branches(10)
    cleanup_csv("branches")

    assert len(df) >= 10
    assert "branch_id" in df.columns
    assert "branch_code" in df.columns
    assert df["branch_code"].is_unique


def test_generate_product_lines():
    """Test product line generation."""
    df = generate_product_lines()
    cleanup_csv("product_lines")

    assert len(df) == 6  # Standard set of products
    assert "product_code" in df.columns
    assert df["product_code"].is_unique


def test_generate_accounts():
    """Test account generation."""
    customers_df = generate_customers(50)
    branches_df = generate_branches(5)
    products_df = generate_product_lines()

    df = generate_accounts(customers_df, branches_df, products_df, 100)
    cleanup_csv("accounts")
    cleanup_csv("customers")
    cleanup_csv("branches")
    cleanup_csv("product_lines")

    assert len(df) == 100
    assert "account_number" in df.columns
    assert df["account_number"].is_unique
    assert (df["customer_id"] <= customers_df["customer_id"].max()).all()


def test_generate_calendar():
    """Test calendar generation."""
    df = generate_calendar(start_year=2023, num_years=1)
    cleanup_csv("calendar")

    assert len(df) >= 365
    assert "full_date" in df.columns
    assert "year" in df.columns
    assert "month" in df.columns


def test_data_types():
    """Test that generated data has correct types."""
    customers = generate_customers(10)
    cleanup_csv("customers")

    assert customers["customer_id"].dtype in ["int64", "int32", "int"]
    assert customers["customer_type"].dtype == "object"
    assert customers["created_date"].dtype == "object"
