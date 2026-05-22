"""Local data loading from CSV/SQLite (fallback when PostgreSQL unavailable)."""

import os
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
import pandas as pd

logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DB = DATA_DIR / "cache.db"  # SQLite cache

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
RAW_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)


@contextmanager
def get_sqlite_connection():
    """Get SQLite connection (creates if not exists)."""
    conn = sqlite3.connect(str(CACHE_DB))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_cache_db():
    """Initialize SQLite cache with schema."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()

        # Create schema to match generated CSV columns
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY,
                account_id INTEGER,
                product_line_id INTEGER,
                branch_id INTEGER,
                transaction_type TEXT,
                amount REAL,
                currency TEXT,
                posting_date TEXT,
                value_date TEXT,
                description TEXT,
                reference TEXT,
                employee_id INTEGER,
                created_date TEXT
            );

            CREATE TABLE IF NOT EXISTS gl_entries (
                gl_entry_id INTEGER PRIMARY KEY,
                transaction_id INTEGER,
                account_id INTEGER,
                gl_account_code TEXT,
                gl_account_name TEXT,
                product_line_id INTEGER,
                debit_amount REAL,
                credit_amount REAL,
                posting_date TEXT,
                value_date TEXT,
                currency TEXT,
                journal_reference TEXT,
                created_date TEXT
            );

            CREATE TABLE IF NOT EXISTS reconciliation_facts (
                reconciliation_id INTEGER PRIMARY KEY,
                transaction_id INTEGER,
                gl_entry_id INTEGER,
                account_id INTEGER,
                product_line_id INTEGER,
                reconciliation_status TEXT,
                severity TEXT,
                source_amount REAL,
                gl_amount REAL,
                amount_difference REAL,
                source_date TEXT,
                gl_date TEXT,
                date_difference_days INTEGER,
                match_confidence REAL DEFAULT 1.0,
                exception_reason TEXT,
                resolved_date TEXT,
                resolved_by TEXT,
                created_date TEXT
            );

            CREATE TABLE IF NOT EXISTS product_lines (
                product_line_id INTEGER PRIMARY KEY,
                product_line_name TEXT,
                product_code TEXT,
                category TEXT,
                created_date TEXT
            );

            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY,
                account_number TEXT,
                customer_id INTEGER,
                branch_id INTEGER,
                product_line_id INTEGER,
                account_type TEXT,
                balance REAL,
                opened_date TEXT,
                is_active BOOLEAN,
                created_date TEXT
            );

            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                customer_name TEXT,
                customer_type TEXT,
                risk_segment TEXT,
                industry TEXT,
                country TEXT,
                created_date TEXT
            );

            CREATE TABLE IF NOT EXISTS branches (
                branch_id INTEGER PRIMARY KEY,
                branch_name TEXT,
                branch_code TEXT,
                country TEXT,
                region TEXT,
                created_date TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(posting_date);
            CREATE INDEX IF NOT EXISTS idx_gl_date ON gl_entries(posting_date);
            CREATE INDEX IF NOT EXISTS idx_recon_status ON reconciliation_facts(reconciliation_status);
            CREATE INDEX IF NOT EXISTS idx_recon_severity ON reconciliation_facts(severity);
        """)
        conn.commit()
        logger.info(f"SQLite cache initialized: {CACHE_DB}")


def load_csv_to_cache():
    """Load CSV files into SQLite cache."""
    init_cache_db()

    with get_sqlite_connection() as conn:
        cursor = conn.cursor()

        # Map CSV files to tables
        csv_tables = {
            "transactions": "transactions",
            "gl_entries": "gl_entries",
            "product_lines": "product_lines",
            "accounts": "accounts",
            "customers": "customers",
            "branches": "branches",
        }

        loaded = []
        for csv_name, table_name in csv_tables.items():
            csv_path = RAW_DIR / f"{csv_name}.csv"

            if not csv_path.exists():
                logger.warning(f"CSV not found: {csv_path}")
                continue

            try:
                df = pd.read_csv(csv_path)

                # Clear existing data
                cursor.execute(f"DELETE FROM {table_name}")

                # Insert new data
                df.to_sql(table_name, conn, if_exists="append", index=False)
                loaded.append((csv_name, len(df)))
                logger.info(f"Loaded {len(df)} rows into {table_name}")

            except Exception as e:
                logger.error(f"Failed to load {csv_name}: {e}")

        conn.commit()
        return loaded


def load_reconciliation_to_cache():
    """Load reconciliation facts if exist."""
    reconciliation_path = RAW_DIR / "reconciliation_facts.csv"

    if not reconciliation_path.exists():
        logger.warning("reconciliation_facts.csv not found, generating from scratch")
        return

    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reconciliation_facts")

        try:
            df = pd.read_csv(reconciliation_path)
            df.to_sql("reconciliation_facts", conn, if_exists="append", index=False)
            conn.commit()
            logger.info(f"Loaded {len(df)} reconciliation facts")
        except Exception as e:
            logger.error(f"Failed to load reconciliation facts: {e}")


def generate_reconciliation_facts():
    """Generate reconciliation facts from transactions and GL entries if not present."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()

        # Check if reconciliation_facts already populated
        cursor.execute("SELECT COUNT(*) FROM reconciliation_facts")
        count = cursor.fetchone()[0]

        if count > 0:
            logger.info(f"Reconciliation facts already loaded: {count} records")
            return

        logger.info("Generating reconciliation facts from transactions and GL entries...")

        # Get all transactions and GL entries
        cursor.execute("SELECT * FROM transactions")
        transactions = {row["transaction_id"]: row for row in cursor.fetchall()}

        cursor.execute("SELECT * FROM gl_entries")
        gl_entries = list(cursor.fetchall())

        matched = 0
        unmatched = 0

        for gl in gl_entries:
            txn_id = gl["transaction_id"]
            status = "MATCHED" if txn_id and txn_id in transactions else "UNMATCHED_SOURCE"
            severity = "HIGH" if status == "UNMATCHED_SOURCE" else "LOW"

            cursor.execute("""
                INSERT INTO reconciliation_facts
                (transaction_id, gl_entry_id, account_id, product_line_id,
                 reconciliation_status, severity, gl_amount, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                txn_id,
                gl["gl_entry_id"],
                gl["account_id"],
                gl["product_line_id"],
                status,
                severity,
                gl["debit_amount"] + gl["credit_amount"],
            ))

            if status == "MATCHED":
                matched += 1
            else:
                unmatched += 1

        conn.commit()
        logger.info(f"Generated reconciliation facts: {matched} matched, {unmatched} unmatched")


def get_sqlite_stats():
    """Get row counts from SQLite cache."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()

        tables = [
            "transactions",
            "gl_entries",
            "reconciliation_facts",
            "accounts",
            "customers",
            "product_lines",
        ]

        stats = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except Exception:
                stats[table] = 0

        return stats


def data_loaded():
    """Check if data is available in cache."""
    if not CACHE_DB.exists():
        return False

    try:
        stats = get_sqlite_stats()
        return stats.get("transactions", 0) > 0 and stats.get("gl_entries", 0) > 0
    except Exception:
        return False


def ensure_data_available():
    """Ensure data is available (load from CSV or generate)."""
    if data_loaded():
        return True

    logger.info("Data not in cache, attempting to load from CSV...")
    load_csv_to_cache()
    generate_reconciliation_facts()

    if data_loaded():
        return True

    logger.warning("Data still not available - user should run data generation")
    return False


# Dashboard query adapters for SQLite mode
def get_total_revenue():
    """Get total revenue sum."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions")
        return cursor.fetchone()[0]


def get_transaction_volume():
    """Get total transaction count."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        return cursor.fetchone()[0]


def get_reconciliation_stats():
    """Get reconciliation match rate."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reconciliation_facts")
        total = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM reconciliation_facts WHERE reconciliation_status = 'matched'"
        )
        matched = cursor.fetchone()[0]

        return {
            'total': total or 1,
            'matched': matched or 0,
            'match_rate': (matched / total * 100) if total > 0 else 0,
        }


def get_monthly_revenue():
    """Get monthly revenue trend as list of dicts."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                strftime('%Y', posting_date) as year,
                strftime('%m', posting_date) as month,
                SUM(amount) as revenue
            FROM transactions
            GROUP BY year, month
            ORDER BY year, month
        """)
        return [
            {
                'year': row[0],
                'month': row[1],
                'revenue': float(row[2] or 0)
            }
            for row in cursor.fetchall()
        ]


def get_product_revenue():
    """Get revenue by product line."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                pl.product_line_name,
                SUM(t.amount) as revenue,
                COUNT(t.transaction_id) as tx_count
            FROM transactions t
            LEFT JOIN product_lines pl ON t.product_line_id = pl.product_line_id
            GROUP BY pl.product_line_name
            ORDER BY revenue DESC
        """)
        return [
            {
                'product_line_name': row[0] or 'Unknown',
                'revenue': float(row[1] or 0),
                'tx_count': int(row[2] or 0),
            }
            for row in cursor.fetchall()
        ]


def get_product_performance():
    """Get product performance metrics."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                pl.product_line_name,
                SUM(t.amount) as revenue,
                COUNT(t.transaction_id) as tx_count,
                AVG(t.amount) as avg_txn
            FROM product_lines pl
            LEFT JOIN transactions t ON t.product_line_id = pl.product_line_id
            GROUP BY pl.product_line_name
            ORDER BY revenue DESC
        """)
        return [
            {
                'product_line_name': row[0] or 'Unknown',
                'revenue': float(row[1] or 0),
                'tx_count': int(row[2] or 0),
                'avg_txn': float(row[3] or 0),
            }
            for row in cursor.fetchall()
        ]


def get_exception_counts():
    """Get exceptions by type."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                reconciliation_status,
                COUNT(*) as count
            FROM reconciliation_facts
            WHERE reconciliation_status != 'MATCHED'
            GROUP BY reconciliation_status
        """)
        return [
            {'reconciliation_status': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]


def get_severity_counts():
    """Get exceptions by severity."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                severity,
                COUNT(*) as count
            FROM reconciliation_facts
            WHERE reconciliation_status != 'MATCHED'
            GROUP BY severity
        """)
        return [
            {'severity': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]


def get_exceptions(severity_filter=None, status_filter=None, limit=100):
    """Get filtered exceptions."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM reconciliation_facts WHERE reconciliation_status != 'MATCHED'"
        params = []

        if severity_filter:
            placeholders = ','.join(['?' for _ in severity_filter])
            query += f" AND severity IN ({placeholders})"
            params.extend(severity_filter)

        if status_filter:
            placeholders = ','.join(['?' for _ in status_filter])
            query += f" AND reconciliation_status IN ({placeholders})"
            params.extend(status_filter)

        query += " LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            {
                'reconciliation_id': row[0],
                'transaction_id': row[1],
                'gl_entry_id': row[2],
                'account_id': row[3],
                'product_line_id': row[4],
                'reconciliation_status': row[5],
                'severity': row[6],
                'source_amount': row[7],
                'gl_amount': row[8],
                'amount_difference': row[9],
                'source_date': row[10],
                'gl_date': row[11],
                'exception_reason': row[12],
                'created_date': row[13],
            }
            for row in rows
        ]


def get_data_counts():
    """Get row counts for all main tables."""
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()

        counts = {}
        tables = [
            'transactions',
            'gl_entries',
            'reconciliation_facts',
            'accounts',
            'customers',
            'product_lines',
        ]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]

        return counts
