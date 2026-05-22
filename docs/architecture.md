# System Architecture

## High-Level Overview

The Banking GL Reconciliation Dashboard is a three-tier application designed for production banking analytics:

```
┌──────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                         │
│  ┌──────────────────┐              ┌──────────────────┐      │
│  │  Streamlit       │              │  FastAPI + Docs  │      │
│  │  Dashboard       │              │  (REST API)      │      │
│  │  5 Pages         │              │  7 Endpoints     │      │
│  └────────┬─────────┘              └────────┬─────────┘      │
└───────────┼──────────────────────────────────┼────────────────┘
            │                                  │
            └──────────────────┬───────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    APPLICATION LAYER                        │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  SQLAlchemy      │         │  Pydantic        │          │
│  │  ORM Models      │         │  Validation      │          │
│  └────────┬─────────┘         └────────┬─────────┘          │
│           │                           │                     │
│  ┌────────▼───────────────────────────▼────────┐            │
│  │  ETL Pipeline Orchestration                 │            │
│  │  • Data Generation                          │            │
│  │  • Bronze Layer Load                        │            │
│  │  • Silver Layer Transform                   │            │
│  │  • Gold Layer Aggregation                   │            │
│  │  • Reconciliation Logic                     │            │
│  └────────┬─────────────────────────────────────┘            │
└───────────┼────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────┐
│                   DATA LAYER (PostgreSQL)                    │
│  ┌──────────────────────────────────────────────┐            │
│  │  BRONZE (Raw Load)                           │            │
│  │  • raw_customers                            │            │
│  │  • raw_transactions                         │            │
│  │  • raw_gl_entries                           │            │
│  └──────────────────────────────────────────────┘            │
│                                                               │
│  ┌──────────────────────────────────────────────┐            │
│  │  SILVER (Cleaned & Standardized)            │            │
│  │  • customers (typed, deduplicated)          │            │
│  │  • transactions (validated)                 │            │
│  │  • gl_entries (normalized)                  │            │
│  └──────────────────────────────────────────────┘            │
│                                                               │
│  ┌──────────────────────────────────────────────┐            │
│  │  GOLD (Analytics Mart)                      │            │
│  │  • kpi_monthly_mart                         │            │
│  │  • reconciliation_fact_mart                 │            │
│  │  • exception_mart                           │            │
│  │  • product_profitability_mart               │            │
│  └──────────────────────────────────────────────┘            │
└────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Data Ingestion (Bronze Layer)

**Input**: Synthetic CSV files from `data/raw/`

Files:
- `customers.csv` (25K rows)
- `accounts.csv` (40K rows)
- `branches.csv` (50 rows)
- `employees.csv` (500 rows)
- `product_lines.csv` (6 rows)
- `transactions.csv` (500K rows)
- `gl_entries.csv` (500K+ rows)

**Process**:
```python
# pipelines/etl_main.py - ETLPipeline.load_*() methods
for each CSV file:
    1. Read CSV into DataFrame
    2. Create ORM objects
    3. Bulk insert into PostgreSQL
```

**Output**: Raw PostgreSQL tables, no transformations

### 2. Silver Layer (Transformations)

**Input**: Raw tables from Bronze

**Transformations**:
- Type enforcement (string → int, date parsing)
- Duplicate detection and removal
- Null value handling
- Data standardization (branch codes, product codes)
- Referential integrity validation

**Current Implementation**: Handled during ETL load process via Pydantic validation in SQLAlchemy

**Output**: Cleaned, validated tables ready for analysis

### 3. Gold Layer (Analytics Marts)

**Input**: Silver layer tables

**Aggregations**:

#### KPI Mart
```sql
SELECT
    EXTRACT(YEAR FROM posting_date) as year,
    EXTRACT(MONTH FROM posting_date) as month,
    SUM(amount) as total_revenue,
    COUNT(*) as transaction_volume,
    (SUM(operating_costs) / SUM(amount)) as cost_to_income_ratio
FROM transactions
GROUP BY year, month
```

#### Reconciliation Fact Mart
```sql
SELECT
    t.transaction_id,
    g.gl_entry_id,
    CASE
        WHEN t.transaction_id = g.transaction_id
            AND ABS(t.amount - g.amount) < 0.01
            THEN 'MATCHED'
        WHEN t.transaction_id IS NULL
            THEN 'UNMATCHED_GL'
        WHEN g.transaction_id IS NULL
            THEN 'UNMATCHED_SOURCE'
        ...
    END as reconciliation_status
FROM transactions t
FULL OUTER JOIN gl_entries g ON t.transaction_id = g.transaction_id
```

#### Exception Mart
```sql
SELECT
    reconciliation_id,
    reconciliation_status,
    CASE
        WHEN reconciliation_status IN ('UNMATCHED_*')
            THEN 'CRITICAL'
        WHEN amount_difference > 10000
            THEN 'HIGH'
        ELSE 'MEDIUM'
    END as severity
FROM reconciliation_facts
WHERE reconciliation_status != 'MATCHED'
```

**Output**: Materialized views/tables optimized for query performance

### 4. Reconciliation Engine

**Core Logic** (`pipelines/etl_main.py` - `ETLPipeline.reconcile_transactions()`):

```python
# Step 1: Exact Match
for each gl_entry with transaction_id:
    if transaction_id exists in transactions:
        create ReconciliationFact(status=MATCHED)

# Step 2: Classify Exceptions
for each unmatched record:
    if transaction missing from GL:
        status = UNMATCHED_GL
        severity = HIGH
    elif GL missing from source:
        status = UNMATCHED_SOURCE
        severity = HIGH
    elif amount difference > 0.01:
        status = AMOUNT_MISMATCH
        severity = MEDIUM/HIGH (based on % diff)
    elif date difference > 2 days:
        status = DATE_MISMATCH
        severity = LOW/MEDIUM
    else:
        status = OTHER_ERROR
        severity = determined by rules

# Step 3: Store ReconciliationFact records
db.add(ReconciliationFact(...))
```

**Matching Rules**:
1. Primary: `transaction_id` exact match
2. Fallback: `account_id + amount + product_line + posting_date (±2 days)`
3. Fuzzy: Amount tolerance = $0.01

**Exception Types**:
- `MATCHED`: Perfect reconciliation
- `UNMATCHED_SOURCE`: Transaction in GL but not in source
- `UNMATCHED_GL`: Transaction in source but not in GL
- `AMOUNT_MISMATCH`: Amounts differ beyond tolerance
- `DATE_MISMATCH`: Posting dates differ > 2 days
- `DUPLICATE_GL`: Multiple GL entries for same transaction
- `PRODUCT_MAPPING_ERROR`: Product line mismatch
- `POTENTIAL_FRAUD_REVIEW`: High-risk pattern detected

## Component Descriptions

### 1. ETL Pipeline (`pipelines/`)

**Files**:
- `generate_synthetic_data.py` - Realistic synthetic data generator
- `etl_main.py` - Main orchestration and transformations
- `data_validation.py` - Data quality checks
- `init_database.py` - Database schema initialization

**Responsibilities**:
- Generate realistic banking data
- Load raw data (Bronze)
- Transform and clean (Silver)
- Create analytics marts (Gold)
- Execute reconciliation logic
- Validate data quality

### 2. API Layer (`app/api/`)

**FastAPI Application** - `main.py`

**Endpoints**:
- `GET /health` - System health check
- `GET /kpis/monthly` - Monthly KPI aggregations
- `GET /kpis/product-line` - Product line performance
- `GET /reconciliation/summary` - Reconciliation metrics
- `GET /reconciliation/exceptions` - Exception list
- `GET /data-quality/summary` - Data quality report
- `GET /pipeline/latest-run` - Last pipeline execution info

**Response Schemas** - `schemas.py`
- Pydantic models for strict validation
- Type hints for IDE support
- Auto-generated OpenAPI docs

### 3. Dashboard Layer (`app/dashboard/`)

**Streamlit Application** - `main.py`

**Pages**:
1. Executive KPI Overview
   - KPI cards (revenue, volume, match rate)
   - Monthly trend line chart
   - Product revenue bar chart

2. Product Line Performance
   - Performance metrics table
   - Product mix pie chart
   - Sort/filter by metric

3. GL Reconciliation Center
   - Match rate KPI
   - Exception breakdown by type
   - Severity distribution

4. Exception Drilldown
   - Interactive filter panel
   - Sortable table
   - CSV export

5. Data Quality Report
   - Row count metrics
   - Validation pass/fail
   - Pipeline metadata

### 4. Data Models (`app/core/models.py`)

**Dimension Tables**:
- `Customer` - Customer master (25K)
- `Account` - Account master (40K)
- `Branch` - Branch locations (50)
- `Employee` - Staff directory (500)
- `ProductLine` - Product catalog (6)
- `Calendar` - Date dimension (730)

**Fact Tables**:
- `Transaction` - Source transactions (500K)
- `GLEntry` - GL postings (500K+)
- `ReconciliationFact` - Matched/unmatched records (500K+)

**Metadata Tables**:
- `DataQualityMetrics` - Validation results
- `PipelineRun` - Execution metadata

## Database Design

### Star Schema for Analytics

```
                    ┌─────────────┐
                    │  Calendar   │
                    └─────────────┘
                          │
        ┌───────┬─────────┼─────────┬──────────┐
        │       │         │         │          │
   ┌────▼──┐ ┌──▼───┐ ┌──▼──────┐ ┌▼────┐ ┌─▼────────┐
   │Customer│ │Branch│ │ProductLine│Account│Transaction│
   └────────┘ └──────┘ └──────────┘ └──────┘ └──────────┘
        │       │         │         │          │
        └───────┴─────────┼─────────┴──────────┘
                          │
                   ┌──────▼────────┐
                   │    Dimension  │
                   │    Tables     │
                   └───────────────┘
                          │
                   ┌──────▼────────┐
                   │  GL Reconcile │
                   │  Fact Tables  │
                   └───────────────┘
```

### Indexing Strategy

**Dimension Tables**:
- PK on natural key (customer_id, account_id, etc.)
- Index on frequently filtered columns (customer_type, risk_segment)

**Fact Tables**:
- PK on surrogate key (transaction_id, gl_entry_id)
- Foreign key indexes for joins
- Date column indexes for time-based queries
- Status/severity indexes for filtering

**Query Optimization**:
- Materialized views for slow aggregations
- Indexes on common filters
- Partitioning by date (if >1B rows)

## Deployment Architecture

### Local Development
```
Laptop/Desktop
├── Python 3.11 venv
├── PostgreSQL (Docker or local)
├── Streamlit dev server (port 8501)
└── FastAPI dev server (port 8000)
```

### Docker Compose
```
Docker Host
├── postgres (port 5432)
├── app (ETL runner)
├── api (port 8000)
└── dashboard (port 8501)
```

### Cloud (Render/Railway)
```
Cloud Platform
├── PostgreSQL (managed)
├── API Service (auto-scaling)
└── Dashboard Service (auto-scaling)
```

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Data generation (500K records) | 5-10s | Depends on CPU |
| ETL load (Bronze→Gold) | 30-60s | Batch insert |
| Reconciliation (500K×500K) | 2-5min | O(n) with indexing |
| Dashboard load | <2s | Materialized views |
| API response | <500ms | Cached queries |

## Security Measures

- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Input validation (Pydantic)
- ✅ Secrets management (environment variables)
- ✅ HTTPS support (via cloud platform)
- ✅ Rate limiting (configurable)
- ✅ CORS headers (configurable)
- ✅ Audit logging capability

## Monitoring & Observability

- **Application Logs**: Python logging module
- **Database Logs**: PostgreSQL query log
- **API Monitoring**: FastAPI middleware
- **Dashboard Metrics**: Streamlit's built-in metrics

---

See [DEPLOYMENT.md](../DEPLOYMENT.md) for cloud deployment details.
