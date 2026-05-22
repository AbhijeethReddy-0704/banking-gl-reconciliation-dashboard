"""Main ETL pipeline - Bronze to Silver to Gold."""

import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.core.models import (
    Customer, Branch, Employee, ProductLine, Account, Transaction,
    GLEntry, Calendar, PipelineRun, ReconciliationFact, ReconciliationStatus, SeverityLevel
)
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)


class ETLPipeline:
    """Main ETL orchestrator."""

    def __init__(self):
        """Initialize pipeline."""
        self.db = SessionLocal()
        self.run_start = datetime.now()
        self.rows_processed = 0
        self.rows_failed = 0

    def log_run(self, status: str, error_message: str = None):
        """Log pipeline run."""
        run_end = datetime.now()
        duration = (run_end - self.run_start).total_seconds()

        run = PipelineRun(
            run_name="etl_main",
            status=status,
            rows_processed=self.rows_processed,
            rows_failed=self.rows_failed,
            start_time=self.run_start,
            end_time=run_end,
            duration_seconds=duration,
            error_message=error_message,
        )
        self.db.add(run)
        self.db.commit()
        logger.info(f"Pipeline run logged: {status} in {duration:.2f}s")

    def load_csv(self, filename: str) -> pd.DataFrame:
        """Load CSV from raw directory."""
        path = Path(f"data/raw/{filename}.csv")
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        logger.info(f"Loading {filename}...")
        return pd.read_csv(path)

    def load_calendar(self):
        """Load calendar dimension."""
        logger.info("Loading calendar...")
        df = self.load_csv("calendar")

        for _, row in df.iterrows():
            calendar = Calendar(
                date_id=int(row["date_id"]),
                full_date=pd.to_datetime(row["full_date"]).date(),
                year=int(row["year"]),
                month=int(row["month"]),
                day=int(row["day"]),
                quarter=int(row["quarter"]),
                week_of_year=int(row["week_of_year"]),
                day_of_week=int(row["day_of_week"]),
                day_name=row["day_name"],
                is_weekend=bool(row["is_weekend"]),
                is_holiday=bool(row["is_holiday"]),
            )
            self.db.add(calendar)
            self.rows_processed += 1

        self.db.commit()
        logger.info(f"Loaded {self.rows_processed} calendar records")

    def load_branches(self):
        """Load branch dimension."""
        logger.info("Loading branches...")
        df = self.load_csv("branches")

        for _, row in df.iterrows():
            branch = Branch(
                branch_id=int(row["branch_id"]),
                branch_name=row["branch_name"],
                branch_code=row["branch_code"],
                country=row["country"],
                region=row["region"],
                created_date=pd.to_datetime(row["created_date"]).date(),
            )
            self.db.add(branch)
            self.rows_processed += 1

        self.db.commit()
        logger.info(f"Loaded {len(df)} branches")

    def load_customers(self):
        """Load customer dimension."""
        logger.info("Loading customers...")
        df = self.load_csv("customers")

        for _, row in df.iterrows():
            customer = Customer(
                customer_id=int(row["customer_id"]),
                customer_name=row["customer_name"],
                customer_type=row["customer_type"],
                industry=row["industry"],
                country=row["country"],
                risk_segment=row["risk_segment"],
                created_date=pd.to_datetime(row["created_date"]).date(),
            )
            self.db.add(customer)
            self.rows_processed += 1

        self.db.commit()
        logger.info(f"Loaded {len(df)} customers")

    def load_employees(self):
        """Load employee dimension."""
        logger.info("Loading employees...")
        df = self.load_csv("employees")

        for _, row in df.iterrows():
            employee = Employee(
                employee_id=int(row["employee_id"]),
                employee_name=row["employee_name"],
                branch_id=int(row["branch_id"]),
                role=row["role"],
                hire_date=pd.to_datetime(row["hire_date"]).date(),
            )
            self.db.add(employee)
            self.rows_processed += 1

        self.db.commit()
        logger.info(f"Loaded {len(df)} employees")

    def load_product_lines(self):
        """Load product line dimension."""
        logger.info("Loading product lines...")
        df = self.load_csv("product_lines")

        for _, row in df.iterrows():
            product_line = ProductLine(
                product_line_id=int(row["product_line_id"]),
                product_line_name=row["product_line_name"],
                product_code=row["product_code"],
                category=row["category"],
                created_date=pd.to_datetime(row["created_date"]).date(),
            )
            self.db.add(product_line)
            self.rows_processed += 1

        self.db.commit()
        logger.info(f"Loaded {len(df)} product lines")

    def load_accounts(self):
        """Load account dimension."""
        logger.info("Loading accounts...")
        df = self.load_csv("accounts")

        for _, row in df.iterrows():
            account = Account(
                account_id=int(row["account_id"]),
                account_number=row["account_number"],
                customer_id=int(row["customer_id"]),
                branch_id=int(row["branch_id"]),
                product_line_id=int(row["product_line_id"]),
                account_type=row["account_type"],
                currency=row["currency"],
                balance=float(row["balance"]),
                opened_date=pd.to_datetime(row["opened_date"]).date(),
                closed_date=None,
                is_active=bool(row["is_active"]),
            )
            self.db.add(account)
            self.rows_processed += 1

        self.db.commit()
        logger.info(f"Loaded {len(df)} accounts")

    def load_transactions(self):
        """Load transaction fact table."""
        logger.info("Loading transactions...")
        df = self.load_csv("transactions")

        for _, row in df.iterrows():
            transaction = Transaction(
                transaction_id=int(row["transaction_id"]),
                account_id=int(row["account_id"]),
                product_line_id=int(row["product_line_id"]),
                branch_id=int(row["branch_id"]),
                transaction_type=row["transaction_type"],
                amount=float(row["amount"]),
                currency=row["currency"],
                posting_date=pd.to_datetime(row["posting_date"]).date(),
                value_date=pd.to_datetime(row["value_date"]).date(),
                description=row["description"],
                reference=row["reference"],
                employee_id=int(row["employee_id"]) if pd.notna(row["employee_id"]) else None,
                created_date=pd.to_datetime(row["created_date"]),
            )
            self.db.add(transaction)
            self.rows_processed += 1

        self.db.commit()
        logger.info(f"Loaded {len(df)} transactions")

    def load_gl_entries(self):
        """Load GL entry fact table."""
        logger.info("Loading GL entries...")
        df = self.load_csv("gl_entries")

        for _, row in df.iterrows():
            gl_entry = GLEntry(
                gl_entry_id=int(row["gl_entry_id"]),
                transaction_id=int(row["transaction_id"]) if pd.notna(row["transaction_id"]) else None,
                account_id=int(row["account_id"]),
                gl_account_code=row["gl_account_code"],
                gl_account_name=row["gl_account_name"],
                product_line_id=int(row["product_line_id"]),
                debit_amount=float(row["debit_amount"]),
                credit_amount=float(row["credit_amount"]),
                posting_date=pd.to_datetime(row["posting_date"]).date(),
                value_date=pd.to_datetime(row["value_date"]).date(),
                currency=row["currency"],
                journal_reference=row["journal_reference"],
                created_date=pd.to_datetime(row["created_date"]),
            )
            self.db.add(gl_entry)
            self.rows_processed += 1

        self.db.commit()
        logger.info(f"Loaded {len(df)} GL entries")

    def reconcile_transactions(self):
        """Reconcile transactions against GL entries."""
        logger.info("Running reconciliation...")

        # Get all transactions and GL entries
        transactions = self.db.query(Transaction).all()
        gl_entries = self.db.query(GLEntry).all()

        transaction_dict = {t.transaction_id: t for t in transactions}
        gl_dict = {g.gl_entry_id: g for g in gl_entries}
        matched_txns = set()
        matched_gls = set()

        # Exact match on transaction_id
        for gl in gl_entries:
            if gl.transaction_id and gl.transaction_id in transaction_dict:
                txn = transaction_dict[gl.transaction_id]
                matched_txns.add(txn.transaction_id)
                matched_gls.add(gl.gl_entry_id)

                # Determine if matched or if there's a mismatch
                gl_amount = gl.debit_amount + gl.credit_amount
                status = ReconciliationStatus.MATCHED
                severity = SeverityLevel.LOW

                if abs(txn.amount - gl_amount) > 0.01:
                    status = ReconciliationStatus.AMOUNT_MISMATCH
                    severity = SeverityLevel.MEDIUM
                elif abs((txn.posting_date - gl.posting_date).days) > 2:
                    status = ReconciliationStatus.DATE_MISMATCH
                    severity = SeverityLevel.LOW

                recon = ReconciliationFact(
                    transaction_id=txn.transaction_id,
                    gl_entry_id=gl.gl_entry_id,
                    account_id=txn.account_id,
                    product_line_id=txn.product_line_id,
                    reconciliation_status=status,
                    severity=severity,
                    source_amount=txn.amount,
                    gl_amount=gl_amount,
                    amount_difference=txn.amount - gl_amount,
                    source_date=txn.posting_date,
                    gl_date=gl.posting_date,
                    date_difference_days=(txn.posting_date - gl.posting_date).days,
                    match_confidence=1.0 if status == ReconciliationStatus.MATCHED else 0.7,
                    exception_reason=None if status == ReconciliationStatus.MATCHED else str(status),
                    created_date=datetime.now(),
                )
                self.db.add(recon)
                self.rows_processed += 1

        # Unmatched transactions
        for txn_id, txn in transaction_dict.items():
            if txn_id not in matched_txns:
                recon = ReconciliationFact(
                    transaction_id=txn.transaction_id,
                    gl_entry_id=None,
                    account_id=txn.account_id,
                    product_line_id=txn.product_line_id,
                    reconciliation_status=ReconciliationStatus.UNMATCHED_GL,
                    severity=SeverityLevel.HIGH,
                    source_amount=txn.amount,
                    gl_amount=None,
                    amount_difference=txn.amount,
                    source_date=txn.posting_date,
                    gl_date=None,
                    date_difference_days=None,
                    match_confidence=0.0,
                    exception_reason="Transaction not found in GL",
                    created_date=datetime.now(),
                )
                self.db.add(recon)
                self.rows_processed += 1

        # Unmatched GL entries
        for gl_id, gl in gl_dict.items():
            if gl_id not in matched_gls and gl.transaction_id is None:
                gl_amount = gl.debit_amount + gl.credit_amount
                recon = ReconciliationFact(
                    transaction_id=None,
                    gl_entry_id=gl.gl_entry_id,
                    account_id=gl.account_id,
                    product_line_id=gl.product_line_id,
                    reconciliation_status=ReconciliationStatus.UNMATCHED_SOURCE,
                    severity=SeverityLevel.HIGH,
                    source_amount=None,
                    gl_amount=gl_amount,
                    amount_difference=gl_amount,
                    source_date=None,
                    gl_date=gl.posting_date,
                    date_difference_days=None,
                    match_confidence=0.0,
                    exception_reason="GL entry not found in transactions",
                    created_date=datetime.now(),
                )
                self.db.add(recon)
                self.rows_processed += 1

        self.db.commit()
        logger.info(f"Reconciliation complete: {self.rows_processed} reconciliation records created")

    def run(self):
        """Run full ETL pipeline."""
        try:
            logger.info("=== Starting ETL Pipeline ===")

            # Initialize database
            init_db()
            logger.info("Database initialized")

            # Load dimensions
            self.load_calendar()
            self.load_branches()
            self.load_customers()
            self.load_employees()
            self.load_product_lines()
            self.load_accounts()

            # Load facts
            self.load_transactions()
            self.load_gl_entries()

            # Run reconciliation
            self.reconcile_transactions()

            logger.info("=== ETL Pipeline Complete ===")
            self.log_run("success")

        except Exception as e:
            logger.error(f"ETL Pipeline failed: {str(e)}", exc_info=True)
            self.log_run("failure", str(e))
            raise
        finally:
            self.db.close()


def main():
    """Main entry point."""
    pipeline = ETLPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
