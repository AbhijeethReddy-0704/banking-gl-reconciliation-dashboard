"""SQLAlchemy ORM models."""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean,
    ForeignKey, Numeric, DECIMAL, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class ReconciliationStatus(str, enum.Enum):
    """Reconciliation status enum."""
    MATCHED = "matched"
    UNMATCHED_SOURCE = "unmatched_source"
    UNMATCHED_GL = "unmatched_gl"
    AMOUNT_MISMATCH = "amount_mismatch"
    DATE_MISMATCH = "date_mismatch"
    DUPLICATE_GL = "duplicate_gl"
    PRODUCT_MAPPING_ERROR = "product_mapping_error"


class SeverityLevel(str, enum.Enum):
    """Exception severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Customer(Base):
    """Customer dimension."""
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True)
    customer_name = Column(String(255), nullable=False)
    customer_type = Column(String(50), nullable=False)  # retail, corporate, institutional
    industry = Column(String(100))
    country = Column(String(100), nullable=False)
    risk_segment = Column(String(50))
    created_date = Column(Date, nullable=False)
    updated_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_customer_type", "customer_type"),
        Index("idx_risk_segment", "risk_segment"),
    )


class Branch(Base):
    """Branch dimension."""
    __tablename__ = "branches"

    branch_id = Column(Integer, primary_key=True)
    branch_name = Column(String(255), nullable=False)
    branch_code = Column(String(10), unique=True, nullable=False)
    country = Column(String(100), nullable=False)
    region = Column(String(100))
    created_date = Column(Date, nullable=False)

    __table_args__ = (
        Index("idx_branch_code", "branch_code"),
    )


class Employee(Base):
    """Employee dimension."""
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True)
    employee_name = Column(String(255), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.branch_id"))
    role = Column(String(100))
    hire_date = Column(Date, nullable=False)


class ProductLine(Base):
    """Product line dimension."""
    __tablename__ = "product_lines"

    product_line_id = Column(Integer, primary_key=True)
    product_line_name = Column(String(100), unique=True, nullable=False)
    product_code = Column(String(20), unique=True, nullable=False)
    category = Column(String(50))
    created_date = Column(Date, nullable=False)

    __table_args__ = (
        Index("idx_product_code", "product_code"),
    )


class Account(Base):
    """Account dimension."""
    __tablename__ = "accounts"

    account_id = Column(Integer, primary_key=True)
    account_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.branch_id"), nullable=False)
    product_line_id = Column(Integer, ForeignKey("product_lines.product_line_id"))
    account_type = Column(String(50))
    currency = Column(String(3), default="USD")
    balance = Column(DECIMAL(18, 2), default=0)
    opened_date = Column(Date, nullable=False)
    closed_date = Column(Date)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_account_number", "account_number"),
        Index("idx_customer_id", "customer_id"),
        Index("idx_account_status", "is_active"),
    )


class Transaction(Base):
    """Transaction fact table."""
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id"), nullable=False)
    product_line_id = Column(Integer, ForeignKey("product_lines.product_line_id"))
    branch_id = Column(Integer, ForeignKey("branches.branch_id"))
    transaction_type = Column(String(50), nullable=False)  # debit, credit
    amount = Column(DECIMAL(18, 2), nullable=False)
    currency = Column(String(3), default="USD")
    posting_date = Column(Date, nullable=False)
    value_date = Column(Date)
    description = Column(String(500))
    reference = Column(String(100))
    employee_id = Column(Integer, ForeignKey("employees.employee_id"))
    created_date = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_account_id", "account_id"),
        Index("idx_posting_date", "posting_date"),
        Index("idx_product_line_id", "product_line_id"),
        Index("idx_transaction_type", "transaction_type"),
    )


class GLEntry(Base):
    """General Ledger entry fact table."""
    __tablename__ = "gl_entries"

    gl_entry_id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"))
    account_id = Column(Integer, ForeignKey("accounts.account_id"))
    gl_account_code = Column(String(20), nullable=False)
    gl_account_name = Column(String(255))
    product_line_id = Column(Integer, ForeignKey("product_lines.product_line_id"))
    debit_amount = Column(DECIMAL(18, 2), default=0)
    credit_amount = Column(DECIMAL(18, 2), default=0)
    posting_date = Column(Date, nullable=False)
    value_date = Column(Date)
    currency = Column(String(3), default="USD")
    journal_reference = Column(String(50))
    created_date = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_gl_account_code", "gl_account_code"),
        Index("idx_gl_posting_date", "posting_date"),
        Index("idx_transaction_link", "transaction_id"),
    )


class ReconciliationFact(Base):
    """Reconciliation fact table."""
    __tablename__ = "reconciliation_facts"

    reconciliation_id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"))
    gl_entry_id = Column(Integer, ForeignKey("gl_entries.gl_entry_id"))
    account_id = Column(Integer, ForeignKey("accounts.account_id"))
    product_line_id = Column(Integer, ForeignKey("product_lines.product_line_id"))
    reconciliation_status = Column(SQLEnum(ReconciliationStatus), nullable=False)
    severity = Column(SQLEnum(SeverityLevel), nullable=False)
    source_amount = Column(DECIMAL(18, 2))
    gl_amount = Column(DECIMAL(18, 2))
    amount_difference = Column(DECIMAL(18, 2))
    source_date = Column(Date)
    gl_date = Column(Date)
    date_difference_days = Column(Integer)
    match_confidence = Column(Float, default=1.0)
    exception_reason = Column(String(500))
    resolved_date = Column(DateTime)
    resolved_by = Column(String(255))
    created_date = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_reconciliation_status", "reconciliation_status"),
        Index("idx_severity", "severity"),
        Index("idx_account_id_recon", "account_id"),
    )


class Calendar(Base):
    """Calendar dimension."""
    __tablename__ = "calendar"

    date_id = Column(Integer, primary_key=True)
    full_date = Column(Date, unique=True, nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    week_of_year = Column(Integer)
    day_of_week = Column(Integer)
    day_name = Column(String(20))
    is_weekend = Column(Boolean)
    is_holiday = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_full_date", "full_date"),
        Index("idx_year_month", "year", "month"),
    )


class DataQualityMetrics(Base):
    """Data quality metrics."""
    __tablename__ = "data_quality_metrics"

    metric_id = Column(Integer, primary_key=True)
    table_name = Column(String(255), nullable=False)
    row_count = Column(Integer)
    null_count = Column(Integer)
    null_percentage = Column(Float)
    duplicate_rows = Column(Integer)
    validation_status = Column(String(50))
    check_timestamp = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_table_name", "table_name"),
        Index("idx_check_timestamp", "check_timestamp"),
    )


class PipelineRun(Base):
    """Pipeline execution metadata."""
    __tablename__ = "pipeline_runs"

    run_id = Column(Integer, primary_key=True)
    run_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # success, failure, running
    rows_processed = Column(Integer)
    rows_failed = Column(Integer)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_seconds = Column(Float)
    error_message = Column(String(1000))

    __table_args__ = (
        Index("idx_run_status", "status"),
        Index("idx_run_time", "start_time"),
    )
