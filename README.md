# Banking KPI & GL Reconciliation Dashboard

![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status: Production](https://img.shields.io/badge/Status-Production--Ready-brightgreen.svg)

A complete end-to-end banking analytics and General Ledger reconciliation platform built with Python, PostgreSQL, FastAPI, and Streamlit. Processes realistic synthetic banking transactions, calculates executive KPIs, reconciles GL entries, and provides an interactive analytics dashboard.

## 📊 Live Demo

- **Dashboard**: [Coming Soon - Deploy to Streamlit Cloud]
- **API**: [Coming Soon - Deploy to Render/Railway]

## 🎯 Project Overview

This project demonstrates production-grade data engineering and analytics capabilities for banking/fintech roles:

- **End-to-end data pipeline**: Bronze → Silver → Gold architecture
- **Real reconciliation logic**: Exact and fuzzy matching with 8+ exception types
- **Executive dashboards**: 5-page Streamlit app with 20+ visualizations
- **REST APIs**: FastAPI with Pydantic validation
- **Fully tested**: 30+ unit and integration tests
- **Cloud-ready**: Docker, CI/CD, deployment configs included

**Problem**: Banks need to reconcile millions of daily transactions against GL entries, identify exceptions, and track KPIs.

**Solution**: Automated platform that processes 500K+ transactions, performs real-time reconciliation, detects anomalies, and surfaces insights via interactive dashboard and APIs.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    RAW DATA LAYER                        │
│  (Synthetic CSVs: customers, accounts, transactions)    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  BRONZE LAYER (Raw Load)                │
│          CSV ingestion → PostgreSQL raw tables          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              SILVER LAYER (Transformation)              │
│   • Data cleaning & type enforcement                    │
│   • Duplicate handling                                   │
│   • Standardization (dates, codes, amounts)            │
│   • Validation rules applied                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│               GOLD LAYER (Analytics Marts)              │
│  • KPI Mart (monthly revenue, CTI, volumes)            │
│  • Reconciliation Fact (matched/unmatched)             │
│  • Exception Mart (classified by type & severity)      │
│  • Product Profitability Mart                          │
│  • Data Quality Summary                                 │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │FastAPI│  │Streamlit│ │Analytics│
    │API    │  │Dashboard│ │Views    │
    └────────┘  └────────┘  └────────┘
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Data Processing** | Pandas, NumPy | ETL transformations |
| **Database** | PostgreSQL | Data storage |
| **ORM** | SQLAlchemy | Database abstraction |
| **Backend API** | FastAPI, Pydantic | REST endpoints, validation |
| **Frontend** | Streamlit, Plotly | Interactive dashboard |
| **Testing** | Pytest, Pytest-cov | Unit & integration tests |
| **Code Quality** | Ruff, MyPy, Black | Linting, typing, formatting |
| **Containerization** | Docker, Docker Compose | Deployment |
| **CI/CD** | GitHub Actions | Automated testing & validation |

## 📁 Project Structure

```
banking-gl-reconciliation-dashboard/
├── app/
│   ├── api/              # FastAPI backend
│   │   ├── main.py       # API endpoints
│   │   └── schemas.py    # Pydantic models
│   ├── core/             # Core utilities
│   │   ├── config.py     # Settings management
│   │   ├── database.py   # DB connections
│   │   └── models.py     # SQLAlchemy ORM
│   └── dashboard/        # Streamlit frontend
│       └── main.py       # Dashboard pages
├── pipelines/            # Data pipelines
│   ├── generate_synthetic_data.py
│   ├── etl_main.py       # Main ETL orchestration
│   └── data_validation.py
├── sql/                  # SQL queries & DDL
│   ├── ddl/             # Schema definitions
│   └── marts/           # Analytics views
├── tests/               # Test suite
│   ├── test_models.py
│   ├── test_api.py
│   └── test_data_generation.py
├── data/                # Data directories
│   ├── raw/            # Generated CSVs
│   └── processed/      # Processed parquets
├── docs/                # Documentation
├── .github/
│   └── workflows/      # GitHub Actions
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+ (optional - fallback to SQLite if unavailable)
- Git

### ⚡ Fastest Start: Local SQLite Mode (Default)

Dashboard works **immediately without any database setup**:

```bash
# Clone repo
git clone <repo-url>
cd banking-gl-reconciliation-dashboard

# Install dependencies
pip install -r requirements.txt

# Generate synthetic data (creates data/raw/*.csv)
python -m pipelines.generate_synthetic_data

# Start dashboard (auto-loads from local cache)
streamlit run streamlit_app.py
```

Dashboard opens at **http://localhost:8501** with:
- ✅ Local SQLite cache (auto-created from CSVs)
- ✅ No PostgreSQL required
- ✅ Data generated on first run if missing
- ✅ Perfect for portfolio, testing, Streamlit Cloud deployment

---

## 📦 Database Modes

### Mode 1: Local SQLite (Default, No Setup Required)

When PostgreSQL is unavailable, dashboard automatically falls back to **SQLite + CSV files**:

```
Data Flow (SQLite Mode):
data/raw/*.csv → SQLite (data/cache.db) → Dashboard
```

**When to use**: Portfolio, demos, testing, Streamlit Cloud

**Auto-detection**: Dashboard checks PostgreSQL on startup. If unavailable, switches to SQLite.

**Status indicator** (sidebar):
- ✅ **Connected to PostgreSQL** = Using PostgreSQL
- 📦 **Using Local SQLite Cache** = Fallback mode

### Mode 2: PostgreSQL (Optional, For Production)

For production deployments with high data volumes:

```
Data Flow (PostgreSQL Mode):
data/raw/*.csv → ETL Pipeline → PostgreSQL → Dashboard/API
```

**Set up PostgreSQL**:

```bash
# Option A: Docker (easiest)
docker compose up postgres -d

# Option B: Local PostgreSQL
createdb banking_db
psql banking_db < sql/ddl/schema.sql

# Option C: Set DATABASE_URL env var
export DATABASE_URL=postgresql://postgres:password@localhost:5432/banking_db
```

**Then generate data and run pipeline**:

```bash
python -m pipelines.generate_synthetic_data
python -m pipelines.etl_main
```

---

### Option 1: Local Setup (With PostgreSQL)

```bash
# Clone repo
git clone <repo-url>
cd banking-gl-reconciliation-dashboard

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install

# Set up database
export DATABASE_URL=postgresql://postgres:password@localhost:5432/banking_db
createdb banking_db

# Generate synthetic data
make generate-data

# Run ETL pipeline
make run-pipeline

# Run tests
make test

# Validate data quality
make validate

# Start API (in one terminal)
make api

# Start Dashboard (in another terminal)
make dashboard
```

Visit:
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

### Option 2: Docker Setup (Recommended)

```bash
# Build and start all services
docker compose up --build

# Wait for initialization (~30 seconds), then visit:
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Dashboard: http://localhost:8501
# API (alternate): http://localhost:8001

# Useful commands
docker compose logs -f app              # Watch logs
docker compose exec app pytest -v       # Run tests
docker compose down                     # Stop all services
```

## 📊 Dashboard Pages

### 1. **Executive KPI Overview**
- Total Revenue (YTD)
- Transaction Volume
- Cost-to-Income Ratio
- Reconciliation Match Rate
- Monthly Revenue Trend (line chart)
- Product Revenue Distribution (bar chart)

### 2. **Product Line Performance**
- Revenue by product (cards, deposits, lending, wealth, mortgage, commercial)
- Transaction counts and averages
- MoM variance analysis
- Top/bottom performers
- Product mix pie chart

### 3. **GL Reconciliation Center**
- Match rate & KPIs
- Exception breakdown by type
- Exceptions by severity
- Unmatched transactions/GL entries
- Amount & date mismatches

### 4. **Exception Drilldown**
- Interactive filtering by severity, type, date range
- Sortable exception table
- CSV export capability
- Root cause analysis

### 5. **Data Quality Report**
- Row counts by table
- Validation check status
- Null rate analysis
- Referential integrity checks
- Pipeline run metadata

## 🔌 API Endpoints

```
GET  /health                          # Health check
GET  /kpis/monthly                    # Monthly KPIs
GET  /kpis/product-line              # Product line performance
GET  /reconciliation/summary          # Reconciliation summary
GET  /reconciliation/exceptions       # Exception list
GET  /data-quality/summary            # Data quality metrics
GET  /pipeline/latest-run             # Latest pipeline execution
```

**Example**:
```bash
curl http://localhost:8000/kpis/monthly | jq .

# Response:
{
  "monthly_kpis": [
    {
      "year": 2023,
      "month": 1,
      "total_revenue": 5234892.50,
      "transaction_volume": 23456,
      "cost_to_income_ratio": 0.25
    }
  ],
  "ytd_revenue": 62818710.00,
  "ytd_transactions": 287654
}
```

## 📈 Reconciliation Logic

The system implements sophisticated matching:

1. **Exact Match**: transaction_id match
2. **Fuzzy Match**: account_id + amount + product_line + date tolerance (2 days)
3. **Exception Classification**:
   - `MATCHED`: Perfect match
   - `UNMATCHED_SOURCE`: Transaction not in GL
   - `UNMATCHED_GL`: GL entry not in transactions
   - `AMOUNT_MISMATCH`: Amounts differ > $0.01
   - `DATE_MISMATCH`: Posting dates differ > 2 days
   - `DUPLICATE_GL`: Multiple GL entries for same transaction
   - `PRODUCT_MAPPING_ERROR`: Product line mismatch

4. **Severity Levels**: Low, Medium, High, Critical

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest --cov=app --cov=pipelines tests/

# Run only API tests
pytest tests/test_api.py -v
```

**Test Coverage**:
- ✅ ORM models (uniqueness, relationships)
- ✅ API endpoints (health, KPIs, reconciliation)
- ✅ Synthetic data generation (volume, types)
- ✅ Data validation rules
- ✅ Reconciliation matching logic
- ✅ Pipeline end-to-end

## 📊 Data Model

```sql
DIMENSION TABLES:
├── customers (25K rows) - Customer master
├── accounts (40K rows) - Account master
├── branches (50 rows) - Branch locations
├── employees (500 rows) - Staff directory
├── product_lines (6 rows) - Product catalog
└── calendar (730 rows) - Date dimension

FACT TABLES:
├── transactions (500K rows) - Source transactions
├── gl_entries (500K rows) - GL postings
└── reconciliation_facts (500K+ rows) - Matched/unmatched records

METRICS TABLES:
├── data_quality_metrics - Validation results
└── pipeline_runs - Execution metadata
```

**Sample Row Counts** (configurable via environment):
```
Customers:        25,000
Accounts:         40,000
Transactions:    500,000
GL Entries:      500,000+
Reconciliation:  500,000+ (varies by match rate)
```

## 🔍 Data Validation

Automated checks:
- ✅ Primary key uniqueness
- ✅ Foreign key referential integrity
- ✅ Non-null constraints on required columns
- ✅ Amount positivity checks
- ✅ Date range validation
- ✅ Debit/credit balance checks
- ✅ Duplicate transaction detection
- ✅ GL account code format validation

## 🚢 Deployment

### Deploy to Streamlit Cloud (Dashboard)

1. Push to GitHub
2. Go to [streamlit.io](https://streamlit.io)
3. Create new app → Connect repo → select `app/dashboard/main.py`
4. Set secrets (DATABASE_URL)

### Deploy to Render (API + Database)

1. Create Render account
2. Use `render.yaml` in repo (one-click deploy)
3. Set environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `NUM_CUSTOMERS`, `NUM_ACCOUNTS`, etc.

### Deploy to Railway

Similar process using `railway.json`

## 📚 Documentation

- **[Architecture](docs/architecture.md)** - System design & data flow
- **[Data Dictionary](docs/data_dictionary.md)** - Table/column definitions
- **[Reconciliation Rules](docs/reconciliation_rules.md)** - Business logic
- **[Deployment Guide](docs/deployment_guide.md)** - Cloud deployment steps
- **[Testing Strategy](docs/testing_strategy.md)** - QA approach
- **[Portfolio Case Study](docs/portfolio_case_study.md)** - Interview talking points

## 🎓 Resume Bullet Points

Use this project to demonstrate:

- ✅ **Data Engineering**: Designed Bronze/Silver/Gold pipeline, 500K+ record ETL
- ✅ **Analytics**: Built KPI dashboard with 20+ metrics across 5 product lines
- ✅ **Reconciliation**: Implemented real matching logic with fuzzy tolerance
- ✅ **Backend APIs**: FastAPI with validation, 7 production endpoints
- ✅ **Frontend**: Streamlit multi-page app with Plotly visualizations
- ✅ **Database**: PostgreSQL schema, ORM modeling, indexes
- ✅ **Testing**: Pytest suite with 30+ tests, CI/CD pipeline
- ✅ **DevOps**: Docker, docker-compose, GitHub Actions, deployment-ready

## 🔐 Security

- ✅ Secrets managed via environment variables
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ No hardcoded credentials
- ✅ CORS headers in API
- ✅ Input validation (Pydantic)
- ✅ Rate limiting ready (add middleware)

## 📋 Key Features

| Feature | Status | Details |
|---------|--------|---------|
| Synthetic Data Gen | ✅ | 500K+ realistic records |
| ETL Pipeline | ✅ | Full Bronze→Gold flow |
| Reconciliation | ✅ | Exact + fuzzy matching |
| Exception Classification | ✅ | 8+ exception types |
| FastAPI Backend | ✅ | 7 endpoints, validation |
| Streamlit Dashboard | ✅ | 5 pages, 20+ charts |
| Testing | ✅ | 30+ unit/integration tests |
| Docker | ✅ | Full compose setup |
| CI/CD | ✅ | GitHub Actions |
| Documentation | ✅ | Full docs/ folder |

## 🚀 Future Improvements

- [ ] Real-time reconciliation via Kafka/streaming
- [ ] Machine learning for anomaly detection
- [ ] Advanced scheduling (Airflow, Prefect)
- [ ] Caching layer (Redis)
- [ ] Alerts/notifications (email, Slack)
- [ ] Advanced reporting (Power BI integration)
- [ ] Audit logging
- [ ] Multi-tenant support

## 📄 License

MIT License - feel free to use for portfolio/learning

## 👤 Author

Built as a production-ready portfolio project for Data Engineer / Analytics Engineer / BI Developer roles.

---

**Questions?** Check the [docs/](docs/) folder or submit an issue.

**Ready to deploy?** See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step cloud deployment.
