"""Generate synthetic banking data."""

import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from faker import Faker
from app.core.config import get_settings

settings = get_settings()
fake = Faker()
random.seed(settings.seed)
np.random.seed(settings.seed)
Faker.seed(settings.seed)

logger = logging.getLogger(__name__)

# Ensure data directories exist
Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("data/processed").mkdir(parents=True, exist_ok=True)

PRODUCT_LINES = [
    ("CARDS", "Credit Cards", "Cards"),
    ("DEPOSITS", "Savings Deposits", "Deposits"),
    ("LENDING", "Personal Loans", "Lending"),
    ("WEALTH", "Wealth Management", "Wealth"),
    ("MORTGAGE", "Mortgage Products", "Lending"),
    ("COMMERCIAL", "Commercial Banking", "Commercial"),
]

COUNTRIES = ["US", "UK", "CA", "AU", "DE"]
RISK_SEGMENTS = ["Low Risk", "Medium Risk", "High Risk", "Very High Risk"]
CUSTOMER_TYPES = ["retail", "corporate", "institutional"]


def generate_customers(n: int) -> pd.DataFrame:
    """Generate customer data."""
    logger.info(f"Generating {n} customers...")

    data = []
    base_date = datetime(2020, 1, 1)

    for i in range(n):
        data.append({
            "customer_id": i + 1,
            "customer_name": fake.name(),
            "customer_type": random.choice(CUSTOMER_TYPES),
            "industry": fake.word(),
            "country": random.choice(COUNTRIES),
            "risk_segment": random.choice(RISK_SEGMENTS),
            "created_date": (base_date + timedelta(days=random.randint(0, 1095))).date(),
        })

    df = pd.DataFrame(data)
    df.to_csv("data/raw/customers.csv", index=False)
    logger.info(f"Created {len(df)} customers")
    return df


def generate_branches(n: int = 50) -> pd.DataFrame:
    """Generate branch data."""
    logger.info(f"Generating {n} branches...")

    data = []
    base_date = datetime(2015, 1, 1)

    for i in range(n):
        data.append({
            "branch_id": i + 1,
            "branch_name": f"{fake.city()} Branch",
            "branch_code": f"BR{i+1:04d}",
            "country": random.choice(COUNTRIES),
            "region": fake.state(),
            "created_date": (base_date + timedelta(days=random.randint(0, 2555))).date(),
        })

    df = pd.DataFrame(data)
    df.to_csv("data/raw/branches.csv", index=False)
    logger.info(f"Created {len(df)} branches")
    return df


def generate_employees(branches_df: pd.DataFrame, n: int = 500) -> pd.DataFrame:
    """Generate employee data."""
    logger.info(f"Generating {n} employees...")

    data = []
    base_date = datetime(2015, 1, 1)

    for i in range(n):
        data.append({
            "employee_id": i + 1,
            "employee_name": fake.name(),
            "branch_id": random.choice(branches_df["branch_id"].values),
            "role": random.choice(["Manager", "Officer", "Teller", "Analyst"]),
            "hire_date": (base_date + timedelta(days=random.randint(0, 2555))).date(),
        })

    df = pd.DataFrame(data)
    df.to_csv("data/raw/employees.csv", index=False)
    logger.info(f"Created {len(df)} employees")
    return df


def generate_product_lines() -> pd.DataFrame:
    """Generate product line data."""
    logger.info("Generating product lines...")

    data = []
    for product_code, product_name, category in PRODUCT_LINES:
        data.append({
            "product_line_id": len(data) + 1,
            "product_line_name": product_name,
            "product_code": product_code,
            "category": category,
            "created_date": datetime(2020, 1, 1).date(),
        })

    df = pd.DataFrame(data)
    df.to_csv("data/raw/product_lines.csv", index=False)
    logger.info(f"Created {len(df)} product lines")
    return df


def generate_accounts(customers_df: pd.DataFrame, branches_df: pd.DataFrame,
                     product_lines_df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Generate account data."""
    logger.info(f"Generating {n} accounts...")

    data = []
    base_date = datetime(2020, 1, 1)

    for i in range(n):
        opened_date = base_date + timedelta(days=random.randint(0, 1460))
        data.append({
            "account_id": i + 1,
            "account_number": f"ACC{i+1:010d}",
            "customer_id": random.choice(customers_df["customer_id"].values),
            "branch_id": random.choice(branches_df["branch_id"].values),
            "product_line_id": random.choice(product_lines_df["product_line_id"].values),
            "account_type": random.choice(["Checking", "Savings", "Investment"]),
            "currency": "USD",
            "balance": round(np.random.lognormal(10, 2), 2),
            "opened_date": opened_date.date(),
            "closed_date": None,
            "is_active": True,
        })

    df = pd.DataFrame(data)
    df.to_csv("data/raw/accounts.csv", index=False)
    logger.info(f"Created {len(df)} accounts")
    return df


def generate_transactions(accounts_df: pd.DataFrame, product_lines_df: pd.DataFrame,
                         branches_df: pd.DataFrame, employees_df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Generate transaction data."""
    logger.info(f"Generating {n} transactions...")

    data = []
    base_date = datetime(2023, 1, 1)

    for i in range(n):
        posting_date = base_date + timedelta(days=random.randint(0, 365))
        data.append({
            "transaction_id": i + 1,
            "account_id": random.choice(accounts_df["account_id"].values),
            "product_line_id": random.choice(product_lines_df["product_line_id"].values),
            "branch_id": random.choice(branches_df["branch_id"].values),
            "transaction_type": random.choice(["debit", "credit"]),
            "amount": round(np.random.exponential(scale=5000), 2),
            "currency": "USD",
            "posting_date": posting_date.date(),
            "value_date": (posting_date + timedelta(days=random.randint(0, 3))).date(),
            "description": f"Transaction {i+1}",
            "reference": f"REF{i+1:010d}",
            "employee_id": random.choice(employees_df["employee_id"].values) if random.random() > 0.3 else None,
            "created_date": posting_date,
        })

    df = pd.DataFrame(data)
    df.to_csv("data/raw/transactions.csv", index=False)
    logger.info(f"Created {len(df)} transactions")
    return df


def generate_gl_entries(transactions_df: pd.DataFrame, accounts_df: pd.DataFrame,
                       product_lines_df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Generate GL entries with intentional exceptions."""
    logger.info(f"Generating {n} GL entries...")

    data = []
    base_date = datetime(2023, 1, 1)

    for i in range(n):
        # 85% matched, 15% exceptions
        if random.random() < 0.85 and i < len(transactions_df):
            # Matched entry
            txn = transactions_df.iloc[i]
            posting_date = txn["posting_date"]
            amount = txn["amount"]
            txn_id = txn["transaction_id"]
        else:
            # Unmatched entry or mismatch
            posting_date = (base_date + timedelta(days=random.randint(0, 365))).date()
            amount = round(np.random.exponential(scale=5000), 2)
            txn_id = None

        # Handle both date and datetime objects
        if isinstance(posting_date, datetime):
            posting_date_val = posting_date.date()
        else:
            posting_date_val = posting_date

        value_date_val = posting_date_val + timedelta(days=random.randint(0, 2))

        data.append({
            "gl_entry_id": i + 1,
            "transaction_id": txn_id,
            "account_id": random.choice(accounts_df["account_id"].values),
            "gl_account_code": f"GL{random.randint(1000, 9999)}",
            "gl_account_name": fake.word(),
            "product_line_id": random.choice(product_lines_df["product_line_id"].values),
            "debit_amount": amount if random.random() > 0.5 else 0,
            "credit_amount": amount if random.random() <= 0.5 else 0,
            "posting_date": posting_date_val,
            "value_date": value_date_val,
            "currency": "USD",
            "journal_reference": f"JNL{i+1:010d}",
            "created_date": datetime.now(),
        })

    df = pd.DataFrame(data)
    df.to_csv("data/raw/gl_entries.csv", index=False)
    logger.info(f"Created {len(df)} GL entries")
    return df


def generate_calendar(start_year: int = 2023, num_years: int = 2) -> pd.DataFrame:
    """Generate calendar dimension."""
    logger.info("Generating calendar dimension...")

    data = []
    start_date = datetime(start_year, 1, 1)
    end_date = start_date + timedelta(days=365*num_years)
    current_date = start_date
    date_id = 1

    while current_date <= end_date:
        data.append({
            "date_id": date_id,
            "full_date": current_date.date(),
            "year": current_date.year,
            "month": current_date.month,
            "day": current_date.day,
            "quarter": (current_date.month - 1) // 3 + 1,
            "week_of_year": current_date.isocalendar()[1],
            "day_of_week": current_date.weekday() + 1,
            "day_name": current_date.strftime("%A"),
            "is_weekend": current_date.weekday() >= 5,
            "is_holiday": False,
        })
        current_date += timedelta(days=1)
        date_id += 1

    df = pd.DataFrame(data)
    df.to_csv("data/raw/calendar.csv", index=False)
    logger.info(f"Created {len(df)} calendar records")
    return df


def main():
    """Generate all synthetic data."""
    import logging
    logging.basicConfig(level=settings.log_level)
    logger.info("Starting synthetic data generation...")

    # Generate dimensions first
    branches_df = generate_branches()
    customers_df = generate_customers(settings.num_customers)
    employees_df = generate_employees(branches_df)
    product_lines_df = generate_product_lines()

    # Generate facts
    accounts_df = generate_accounts(customers_df, branches_df, product_lines_df, settings.num_accounts)
    transactions_df = generate_transactions(accounts_df, product_lines_df, branches_df, employees_df,
                                           settings.num_transactions)
    gl_entries_df = generate_gl_entries(transactions_df, accounts_df, product_lines_df,
                                       settings.num_gl_entries)

    # Generate calendar
    generate_calendar(start_year=2023, num_years=2)

    logger.info("Synthetic data generation complete!")
    logger.info(f"Data saved to data/raw/ directory")


if __name__ == "__main__":
    main()
