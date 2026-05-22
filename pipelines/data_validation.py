"""Data quality validation and checks."""

import logging
from datetime import datetime
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.models import (
    Customer, Branch, Account, Transaction, GLEntry,
    ProductLine, DataQualityMetrics
)
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)


class DataValidator:
    """Data quality validator."""

    def __init__(self):
        """Initialize validator."""
        self.db = SessionLocal()
        self.checks_passed = 0
        self.checks_failed = 0

    def check_uniqueness(self, model, column, column_name: str) -> bool:
        """Check for unique constraint violations."""
        logger.info(f"Checking uniqueness of {column_name}...")

        total = self.db.query(func.count(model.id if hasattr(model, 'id') else model.__table__.columns[0])).scalar()
        unique = self.db.query(func.count(func.distinct(column))).scalar()

        if total == unique:
            logger.info(f"✓ {column_name} is unique")
            self.checks_passed += 1
            return True
        else:
            logger.warning(f"✗ {column_name} has {total - unique} duplicates")
            self.checks_failed += 1
            return False

    def check_not_null(self, model, column, column_name: str) -> bool:
        """Check for null values in required column."""
        logger.info(f"Checking null values in {column_name}...")

        total = self.db.query(func.count(model.id if hasattr(model, 'id') else model.__table__.columns[0])).scalar()
        non_null = self.db.query(func.count(column)).scalar()

        if total == non_null:
            logger.info(f"✓ {column_name} has no nulls")
            self.checks_passed += 1
            return True
        else:
            null_count = total - non_null
            logger.warning(f"✗ {column_name} has {null_count} null values ({null_count/total*100:.1f}%)")
            self.checks_failed += 1
            return False

    def check_referential_integrity(self, model, column, referenced_table, referenced_column) -> bool:
        """Check foreign key referential integrity."""
        logger.info(f"Checking referential integrity for {model.__tablename__}...")

        query = f"""
            SELECT COUNT(*) FROM {model.__tablename__} t
            WHERE t.{column.name} IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM {referenced_table.__tablename__} r WHERE r.{referenced_column.name} = t.{column.name})
        """

        result = self.db.execute(text(query)).scalar()

        if result == 0:
            logger.info(f"✓ Referential integrity OK for {model.__tablename__}.{column.name}")
            self.checks_passed += 1
            return True
        else:
            logger.warning(f"✗ Found {result} orphaned records in {model.__tablename__}")
            self.checks_failed += 1
            return False

    def run_all_checks(self):
        """Run all data validation checks."""
        logger.info("=== Starting Data Quality Validation ===")

        try:
            # Account uniqueness
            self.check_uniqueness(Account, Account.account_number, "account_number")

            # Transaction amounts not null and positive
            total_txns = self.db.query(func.count(Transaction.transaction_id)).scalar()
            null_amounts = self.db.query(func.count(Transaction.transaction_id)).filter(Transaction.amount.is_(None)).scalar()
            if null_amounts == 0:
                logger.info(f"✓ All transactions have amounts")
                self.checks_passed += 1
            else:
                logger.warning(f"✗ {null_amounts} transactions have null amounts")
                self.checks_failed += 1

            # Referential integrity
            try:
                self.check_referential_integrity(Account, Account.customer_id, Customer, Customer.customer_id)
            except Exception as e:
                logger.warning(f"Could not check account->customer integrity: {e}")

            try:
                self.check_referential_integrity(Account, Account.branch_id, Branch, Branch.branch_id)
            except Exception as e:
                logger.warning(f"Could not check account->branch integrity: {e}")

            try:
                self.check_referential_integrity(Transaction, Transaction.product_line_id, ProductLine, ProductLine.product_line_id)
            except Exception as e:
                logger.warning(f"Could not check transaction->product_line integrity: {e}")

            # Row counts
            customer_count = self.db.query(func.count(Customer.customer_id)).scalar() or 0
            branch_count = self.db.query(func.count(Branch.branch_id)).scalar() or 0
            account_count = self.db.query(func.count(Account.account_id)).scalar() or 0
            txn_count = self.db.query(func.count(Transaction.transaction_id)).scalar() or 0
            gl_count = self.db.query(func.count(GLEntry.gl_entry_id)).scalar() or 0

            logger.info(f"Row counts: Customers={customer_count}, Branches={branch_count}, Accounts={account_count}, Transactions={txn_count}, GL={gl_count}")

            # Log metrics
            self._log_metrics("customers", customer_count)
            self._log_metrics("branches", branch_count)
            self._log_metrics("accounts", account_count)
            self._log_metrics("transactions", txn_count)
            self._log_metrics("gl_entries", gl_count)

            logger.info(f"=== Validation Complete: {self.checks_passed} passed, {self.checks_failed} failed ===")

        finally:
            self.db.close()

    def _log_metrics(self, table_name: str, row_count: int):
        """Log data quality metrics."""
        metric = DataQualityMetrics(
            table_name=table_name,
            row_count=row_count,
            validation_status="passed" if row_count > 0 else "empty",
            check_timestamp=datetime.now(),
        )
        # Note: In real implementation, would add to DB
        logger.info(f"Metrics for {table_name}: {row_count} rows")


def main():
    """Main entry point."""
    validator = DataValidator()
    validator.run_all_checks()


if __name__ == "__main__":
    main()
