# Data Dictionary

## Dimension Tables

### customers
Master customer data

| Column | Type | Description |
|--------|------|-------------|
| customer_id | INT | PK: Unique customer identifier |
| customer_name | VARCHAR(255) | Customer full name |
| customer_type | VARCHAR(50) | retail, corporate, institutional |
| industry | VARCHAR(100) | Industry classification |
| country | VARCHAR(100) | Country of residence |
| risk_segment | VARCHAR(50) | Low/Medium/High/Very High Risk |
| created_date | DATE | Customer onboarding date |
| updated_date | TIMESTAMP | Last update timestamp |

**Cardinality**: 25,000 rows | **Update Frequency**: Monthly

---

### accounts
Account master with customer and product relationships

| Column | Type | Description |
|--------|------|-------------|
| account_id | INT | PK: Unique account identifier |
| account_number | VARCHAR(50) | Customer-facing account number (UNIQUE) |
| customer_id | INT | FK: Reference to customers |
| branch_id | INT | FK: Reference to branches |
| product_line_id | INT | FK: Reference to product_lines |
| account_type | VARCHAR(50) | Checking, Savings, Investment, etc. |
| currency | VARCHAR(3) | ISO currency code (default: USD) |
| balance | DECIMAL(18,2) | Current account balance |
| opened_date | DATE | Account opening date |
| closed_date | DATE | Account closure date (NULL if open) |
| is_active | BOOLEAN | Account status (active/inactive) |

**Cardinality**: 40,000 rows | **Update Frequency**: Real-time

---

### branches
Physical branch locations

| Column | Type | Description |
|--------|------|-------------|
| branch_id | INT | PK: Unique branch identifier |
| branch_name | VARCHAR(255) | Branch location name |
| branch_code | VARCHAR(10) | Unique branch code (e.g., BR0001) |
| country | VARCHAR(100) | Country location |
| region | VARCHAR(100) | State/province/region |
| created_date | DATE | Branch establishment date |

**Cardinality**: 50 rows | **Update Frequency**: Yearly

---

### employees
Staff directory

| Column | Type | Description |
|--------|------|-------------|
| employee_id | INT | PK: Unique employee identifier |
| employee_name | VARCHAR(255) | Employee full name |
| branch_id | INT | FK: Employee's home branch |
| role | VARCHAR(100) | Manager, Officer, Teller, Analyst, etc. |
| hire_date | DATE | Employment start date |

**Cardinality**: 500 rows | **Update Frequency**: Monthly

---

### product_lines
Product catalog

| Column | Type | Description |
|--------|------|-------------|
| product_line_id | INT | PK: Unique product line ID |
| product_line_name | VARCHAR(100) | Product name (e.g., "Credit Cards") |
| product_code | VARCHAR(20) | Internal product code (e.g., "CARDS") |
| category | VARCHAR(50) | Broad category (Cards, Deposits, Lending, etc.) |
| created_date | DATE | Product launch date |

**Cardinality**: 6 rows | **Update Frequency**: Quarterly

**Standard Products**:
- CARDS: Credit Cards
- DEPOSITS: Savings Deposits
- LENDING: Personal Loans
- WEALTH: Wealth Management
- MORTGAGE: Mortgage Products
- COMMERCIAL: Commercial Banking

---

### calendar
Date dimension for time-based analysis

| Column | Type | Description |
|--------|------|-------------|
| date_id | INT | PK: Unique date identifier |
| full_date | DATE | Actual calendar date (UNIQUE) |
| year | INT | Calendar year |
| month | INT | Month number (1-12) |
| day | INT | Day of month (1-31) |
| quarter | INT | Quarter (1-4) |
| week_of_year | INT | ISO week number |
| day_of_week | INT | Day number (1=Monday, 7=Sunday) |
| day_name | VARCHAR(20) | Day name (Monday, Tuesday, etc.) |
| is_weekend | BOOLEAN | TRUE if Saturday/Sunday |
| is_holiday | BOOLEAN | TRUE if bank holiday |

**Cardinality**: 730 rows (2 years) | **Update Frequency**: Static

---

## Fact Tables

### transactions
Source system transactions

| Column | Type | Description |
|--------|------|-------------|
| transaction_id | INT | PK: Unique transaction ID |
| account_id | INT | FK: Account where transaction occurred |
| product_line_id | INT | FK: Product line association |
| branch_id | INT | FK: Processing branch |
| transaction_type | VARCHAR(50) | debit, credit |
| amount | DECIMAL(18,2) | Transaction amount |
| currency | VARCHAR(3) | Currency code (default: USD) |
| posting_date | DATE | Date transaction posted |
| value_date | DATE | Date funds are available |
| description | VARCHAR(500) | Transaction description |
| reference | VARCHAR(100) | Reference number |
| employee_id | INT | FK: Processing employee (nullable) |
| created_date | TIMESTAMP | Record creation timestamp |

**Cardinality**: 500,000 rows | **Frequency**: Daily | **Latency**: 1-2 hours

**Typical Volume**: 5,000+ transactions/day

---

### gl_entries
General Ledger postings

| Column | Type | Description |
|--------|------|-------------|
| gl_entry_id | INT | PK: Unique GL entry ID |
| transaction_id | INT | FK: Source transaction (nullable) |
| account_id | INT | FK: GL account source |
| gl_account_code | VARCHAR(20) | GL chart of accounts code |
| gl_account_name | VARCHAR(255) | GL account description |
| product_line_id | INT | FK: Product classification |
| debit_amount | DECIMAL(18,2) | Debit posting amount |
| credit_amount | DECIMAL(18,2) | Credit posting amount |
| posting_date | DATE | GL posting date |
| value_date | DATE | GL value date |
| currency | VARCHAR(3) | Currency code |
| journal_reference | VARCHAR(50) | Journal batch reference |
| created_date | TIMESTAMP | Record creation timestamp |

**Cardinality**: 500,000+ rows | **Frequency**: Daily | **Latency**: 2-4 hours

**Note**: Typically 1-2 GL entries per transaction (debit + credit)

---

### reconciliation_facts
Reconciliation matching results

| Column | Type | Description |
|--------|------|-------------|
| reconciliation_id | INT | PK: Unique reconciliation ID |
| transaction_id | INT | FK: Source transaction (nullable) |
| gl_entry_id | INT | FK: GL entry (nullable) |
| account_id | INT | FK: Associated account |
| product_line_id | INT | FK: Product line |
| reconciliation_status | VARCHAR(50) | MATCHED, UNMATCHED_SOURCE, UNMATCHED_GL, AMOUNT_MISMATCH, DATE_MISMATCH, DUPLICATE_GL, PRODUCT_MAPPING_ERROR |
| severity | VARCHAR(50) | low, medium, high, critical |
| source_amount | DECIMAL(18,2) | Amount from source transaction |
| gl_amount | DECIMAL(18,2) | Amount from GL entry |
| amount_difference | DECIMAL(18,2) | Absolute difference |
| source_date | DATE | Source transaction date |
| gl_date | DATE | GL posting date |
| date_difference_days | INT | Days between posting |
| match_confidence | FLOAT | 0.0-1.0 confidence score |
| exception_reason | VARCHAR(500) | Explanation for non-match |
| resolved_date | TIMESTAMP | When exception was resolved |
| resolved_by | VARCHAR(255) | Who resolved the exception |
| created_date | TIMESTAMP | Record creation timestamp |

**Cardinality**: 500,000+ rows | **Frequency**: Daily | **Latency**: 4-6 hours

---

## Metadata Tables

### data_quality_metrics
Data quality check results

| Column | Type | Description |
|--------|------|-------------|
| metric_id | INT | PK: Unique metric ID |
| table_name | VARCHAR(255) | Target table name |
| row_count | INT | Number of rows in table |
| null_count | INT | Number of NULL values |
| null_percentage | FLOAT | Percentage of NULLs |
| duplicate_rows | INT | Number of duplicate records |
| validation_status | VARCHAR(50) | passed, failed, warning |
| check_timestamp | TIMESTAMP | When check was run |

**Purpose**: Track data quality metrics over time

---

### pipeline_runs
ETL pipeline execution history

| Column | Type | Description |
|--------|------|-------------|
| run_id | INT | PK: Unique run identifier |
| run_name | VARCHAR(255) | Pipeline name (e.g., etl_main) |
| status | VARCHAR(50) | success, failure, running |
| rows_processed | INT | Number of rows processed |
| rows_failed | INT | Number of rows that failed |
| start_time | TIMESTAMP | Pipeline start time |
| end_time | TIMESTAMP | Pipeline completion time |
| duration_seconds | FLOAT | Total execution time |
| error_message | VARCHAR(1000) | Error details if failed |

**Purpose**: Monitor pipeline performance and troubleshoot failures

---

## Derived Metrics

### KPI: Revenue
```
SUM(transactions.amount) WHERE transaction_type = 'credit'
```

### KPI: Cost-to-Income Ratio
```
SUM(operating_costs) / SUM(revenue)
```

### KPI: Reconciliation Match Rate
```
COUNT(MATCHED) / COUNT(ALL) * 100%
```

### KPI: Exception Rate
```
COUNT(exceptions) / COUNT(total) * 100%
```

### KPI: Transaction Volume
```
COUNT(transactions)
```

---

## Data Quality Rules

| Rule | Column(s) | Constraint | Severity |
|------|-----------|-----------|----------|
| PK Uniqueness | account_id | UNIQUE | Critical |
| PK Uniqueness | transaction_id | UNIQUE | Critical |
| PK Uniqueness | gl_entry_id | UNIQUE | Critical |
| FK Referential | account_id → accounts | Foreign Key | High |
| FK Referential | customer_id → customers | Foreign Key | High |
| Not Null | amount (transactions) | NOT NULL | High |
| Not Null | amount (gl_entries) | NOT NULL | High |
| Amount > 0 | amount | > 0 | Medium |
| Date Range | posting_date | Between 2023-01-01 and TODAY | High |
| Debit/Credit Balance | GL entries | ABS(SUM(debit) - SUM(credit)) < threshold | Medium |

---

## Sample Aggregations

### Monthly Revenue by Product
```sql
SELECT
    p.product_line_name,
    EXTRACT(YEAR FROM t.posting_date) as year,
    EXTRACT(MONTH FROM t.posting_date) as month,
    SUM(t.amount) as total_revenue,
    COUNT(*) as transaction_count
FROM transactions t
JOIN product_lines p ON t.product_line_id = p.product_line_id
WHERE t.transaction_type = 'credit'
GROUP BY p.product_line_name, year, month
ORDER BY year, month, total_revenue DESC
```

### Reconciliation Exception Summary
```sql
SELECT
    r.reconciliation_status,
    r.severity,
    COUNT(*) as exception_count,
    SUM(ABS(r.amount_difference)) as total_amount_variance
FROM reconciliation_facts r
WHERE r.reconciliation_status != 'MATCHED'
GROUP BY r.reconciliation_status, r.severity
ORDER BY exception_count DESC
```

### Data Quality Report
```sql
SELECT
    d.table_name,
    d.row_count,
    d.null_count,
    ROUND(d.null_percentage, 2) as null_pct,
    d.validation_status,
    d.check_timestamp
FROM data_quality_metrics d
WHERE d.check_timestamp = (SELECT MAX(check_timestamp) FROM data_quality_metrics)
ORDER BY d.table_name
```

---

## Update Frequency & Latency

| Table | Frequency | Latency | Volatility |
|-------|-----------|---------|-----------|
| customers | Monthly | N/A | Low |
| accounts | Real-time | None | Low |
| transactions | Daily | 1-2h | High |
| gl_entries | Daily | 2-4h | High |
| reconciliation_facts | Daily | 4-6h | Medium |
| calendar | Static | N/A | None |

---

For more details, see [architecture.md](architecture.md).
