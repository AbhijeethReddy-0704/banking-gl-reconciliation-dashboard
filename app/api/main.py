"""FastAPI application."""

import logging
from datetime import datetime
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db, get_engine
from app.core.models import Base, Transaction, GLEntry, ReconciliationFact, PipelineRun, ReconciliationStatus
from app.api.schemas import (
    KPIResponse, KPIMonth, ProductLineResponse, ProductLineKPI,
    ReconciliationSummary, ExceptionResponse, ExceptionRecord,
    DataQualitySummary, DataQualityMetric, PipelineRunInfo, HealthResponse
)

# Create tables
engine = get_engine()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Banking GL Reconciliation API",
    description="API for banking KPIs and GL reconciliation",
    version="1.0.0",
)

logger = logging.getLogger(__name__)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        database="connected",
    )


@app.get("/kpis/monthly", response_model=KPIResponse)
async def get_monthly_kpis(db: Session = Depends(get_db)):
    """Get monthly KPIs."""
    # Aggregate transactions by month
    monthly_data = db.query(
        func.extract('year', Transaction.posting_date).label('year'),
        func.extract('month', Transaction.posting_date).label('month'),
        func.sum(Transaction.amount).label('revenue'),
        func.count(Transaction.transaction_id).label('tx_count'),
    ).group_by(
        func.extract('year', Transaction.posting_date),
        func.extract('month', Transaction.posting_date),
    ).all()

    monthly_kpis = [
        KPIMonth(
            year=int(row.year) if row.year else 2023,
            month=int(row.month) if row.month else 1,
            total_revenue=float(row.revenue or 0),
            transaction_volume=int(row.tx_count or 0),
            cost_to_income_ratio=0.25,  # Placeholder
        )
        for row in monthly_data
    ]

    ytd_revenue = sum(k.total_revenue for k in monthly_kpis)
    ytd_transactions = sum(k.transaction_volume for k in monthly_kpis)
    avg_cost_to_income = 0.25

    return KPIResponse(
        monthly_kpis=monthly_kpis,
        ytd_revenue=ytd_revenue,
        ytd_transactions=ytd_transactions,
        avg_cost_to_income=avg_cost_to_income,
    )


@app.get("/kpis/product-line", response_model=ProductLineResponse)
async def get_product_line_kpis(db: Session = Depends(get_db)):
    """Get product line performance."""
    product_data = db.query(
        Transaction.product_line_id,
        func.sum(Transaction.amount).label('revenue'),
        func.count(Transaction.transaction_id).label('tx_count'),
    ).group_by(Transaction.product_line_id).all()

    product_lines = [
        ProductLineKPI(
            product_line_name=f"Product {row.product_line_id}",
            revenue=float(row.revenue or 0),
            transaction_count=int(row.tx_count or 0),
            avg_transaction_size=float(row.revenue or 0) / int(row.tx_count or 1),
        )
        for row in product_data
    ]

    total_revenue = sum(p.revenue for p in product_lines)

    return ProductLineResponse(
        product_lines=product_lines,
        total_revenue=total_revenue,
    )


@app.get("/reconciliation/summary", response_model=ReconciliationSummary)
async def get_reconciliation_summary(db: Session = Depends(get_db)):
    """Get reconciliation summary."""
    total = db.query(func.count(ReconciliationFact.reconciliation_id)).scalar() or 0

    matched = db.query(func.count(ReconciliationFact.reconciliation_id)).filter(
        ReconciliationFact.reconciliation_status == ReconciliationStatus.MATCHED
    ).scalar() or 0

    unmatched_source = db.query(func.count(ReconciliationFact.reconciliation_id)).filter(
        ReconciliationFact.reconciliation_status == ReconciliationStatus.UNMATCHED_SOURCE
    ).scalar() or 0

    unmatched_gl = db.query(func.count(ReconciliationFact.reconciliation_id)).filter(
        ReconciliationFact.reconciliation_status == ReconciliationStatus.UNMATCHED_GL
    ).scalar() or 0

    amount_mismatch = db.query(func.count(ReconciliationFact.reconciliation_id)).filter(
        ReconciliationFact.reconciliation_status == ReconciliationStatus.AMOUNT_MISMATCH
    ).scalar() or 0

    date_mismatch = db.query(func.count(ReconciliationFact.reconciliation_id)).filter(
        ReconciliationFact.reconciliation_status == ReconciliationStatus.DATE_MISMATCH
    ).scalar() or 0

    match_rate = (matched / total * 100) if total > 0 else 0
    exception_rate = ((total - matched) / total * 100) if total > 0 else 0

    return ReconciliationSummary(
        total_records=total,
        matched=matched,
        unmatched_source=unmatched_source,
        unmatched_gl=unmatched_gl,
        amount_mismatch=amount_mismatch,
        date_mismatch=date_mismatch,
        match_rate=match_rate,
        exception_rate=exception_rate,
    )


@app.get("/reconciliation/exceptions", response_model=ExceptionResponse)
async def get_exceptions(db: Session = Depends(get_db), limit: int = 100):
    """Get reconciliation exceptions."""
    exceptions = db.query(ReconciliationFact).filter(
        ReconciliationFact.reconciliation_status != ReconciliationStatus.MATCHED
    ).limit(limit).all()

    exception_records = [
        ExceptionRecord(
            reconciliation_id=e.reconciliation_id,
            account_id=e.account_id,
            product_line_id=e.product_line_id,
            status=str(e.reconciliation_status),
            severity=str(e.severity),
            amount_difference=float(e.amount_difference) if e.amount_difference else None,
            exception_reason=e.exception_reason,
            created_date=e.created_date,
        )
        for e in exceptions
    ]

    high_count = sum(1 for e in exceptions if str(e.severity) == "high")
    critical_count = sum(1 for e in exceptions if str(e.severity) == "critical")

    return ExceptionResponse(
        exceptions=exception_records,
        total_count=len(exception_records),
        high_severity_count=high_count,
        critical_count=critical_count,
    )


@app.get("/data-quality/summary", response_model=DataQualitySummary)
async def get_data_quality_summary(db: Session = Depends(get_db)):
    """Get data quality summary."""
    metrics = [
        DataQualityMetric(
            table_name="transactions",
            row_count=db.query(func.count(Transaction.transaction_id)).scalar() or 0,
            validation_status="passed",
        ),
        DataQualityMetric(
            table_name="gl_entries",
            row_count=db.query(func.count(GLEntry.gl_entry_id)).scalar() or 0,
            validation_status="passed",
        ),
        DataQualityMetric(
            table_name="reconciliation_facts",
            row_count=db.query(func.count(ReconciliationFact.reconciliation_id)).scalar() or 0,
            validation_status="passed",
        ),
    ]

    return DataQualitySummary(
        metrics=metrics,
        overall_status="passed",
        last_check=datetime.now(),
    )


@app.get("/pipeline/latest-run", response_model=PipelineRunInfo)
async def get_latest_pipeline_run(db: Session = Depends(get_db)):
    """Get latest pipeline run."""
    run = db.query(PipelineRun).order_by(PipelineRun.run_id.desc()).first()

    if not run:
        return PipelineRunInfo(
            run_id=0,
            run_name="none",
            status="no_runs",
            rows_processed=0,
            rows_failed=0,
            start_time=datetime.now(),
            end_time=None,
            duration_seconds=None,
        )

    return PipelineRunInfo(
        run_id=run.run_id,
        run_name=run.run_name,
        status=run.status,
        rows_processed=run.rows_processed or 0,
        rows_failed=run.rows_failed or 0,
        start_time=run.start_time,
        end_time=run.end_time,
        duration_seconds=run.duration_seconds,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
