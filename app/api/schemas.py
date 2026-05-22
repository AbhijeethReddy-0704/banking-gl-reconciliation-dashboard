"""Pydantic response schemas."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel


class KPIMonth(BaseModel):
    """Monthly KPI data."""
    year: int
    month: int
    total_revenue: float
    transaction_volume: int
    cost_to_income_ratio: float


class KPIResponse(BaseModel):
    """KPI response."""
    monthly_kpis: List[KPIMonth]
    ytd_revenue: float
    ytd_transactions: int
    avg_cost_to_income: float


class ProductLineKPI(BaseModel):
    """Product line KPI."""
    product_line_name: str
    revenue: float
    transaction_count: int
    avg_transaction_size: float


class ProductLineResponse(BaseModel):
    """Product line performance response."""
    product_lines: List[ProductLineKPI]
    total_revenue: float


class ReconciliationSummary(BaseModel):
    """Reconciliation summary."""
    total_records: int
    matched: int
    unmatched_source: int
    unmatched_gl: int
    amount_mismatch: int
    date_mismatch: int
    match_rate: float
    exception_rate: float


class ExceptionRecord(BaseModel):
    """Exception record."""
    reconciliation_id: int
    account_id: int
    product_line_id: Optional[int]
    status: str
    severity: str
    amount_difference: Optional[float]
    exception_reason: Optional[str]
    created_date: datetime


class ExceptionResponse(BaseModel):
    """Exception list response."""
    exceptions: List[ExceptionRecord]
    total_count: int
    high_severity_count: int
    critical_count: int


class DataQualityMetric(BaseModel):
    """Data quality metric."""
    table_name: str
    row_count: int
    validation_status: str


class DataQualitySummary(BaseModel):
    """Data quality summary."""
    metrics: List[DataQualityMetric]
    overall_status: str
    last_check: datetime


class PipelineRunInfo(BaseModel):
    """Pipeline run information."""
    run_id: int
    run_name: str
    status: str
    rows_processed: int
    rows_failed: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    database: str
