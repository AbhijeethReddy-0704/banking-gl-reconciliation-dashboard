# Streamlit Dashboard Setup

## Quick Start

Run from project root:

```bash
cd C:\Users\abhij\banking-gl-reconciliation-dashboard
streamlit run streamlit_app.py
```

**Local URL**: `http://localhost:8501`

---

## Prerequisites

1. **Python packages installed**:
   ```bash
   pip install -r requirements.txt
   ```

2. **PostgreSQL running** (with database initialized):
   ```bash
   # Via Docker Compose (easiest)
   docker compose up postgres -d
   
   # Or manually
   createdb banking_db
   psql banking_db < sql/ddl/schema.sql
   ```

3. **Data generated and loaded** (optional, dashboard works with empty DB):
   ```bash
   python -m pipelines.generate_synthetic_data
   python -m pipelines.etl_main
   ```

---

## Setup Details

### Root Entry Point: `streamlit_app.py`

This file:
- Adds project root to Python path (allows imports to work)
- Sets environment variables
- Imports dashboard main function from `app/dashboard/main.py`
- Runs the Streamlit app

### Configuration: `.streamlit/config.toml`

Streamlit settings:
- Theme: Blue/white corporate theme
- Port: 8501
- Run-on-save: enabled
- Error details: shown

### Database Connection

Dashboard connects via:
```python
from app.core.database import SessionLocal
db = SessionLocal()  # Uses DATABASE_URL from environment
```

**Set DATABASE_URL**:
```bash
export DATABASE_URL=postgresql://postgres:password@localhost:5432/banking_db
```

Or create `.env` file:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/banking_db
```

---

## Running Streamlit

### Option 1: From Project Root (Recommended)
```bash
cd C:\Users\abhij\banking-gl-reconciliation-dashboard
streamlit run streamlit_app.py
```

### Option 2: Using Makefile
```bash
make dashboard
```

### Option 3: Using Docker
```bash
docker compose up dashboard
```

---

## Dashboard Pages

Once running, access at **http://localhost:8501**

1. **Executive KPI Overview**
   - Total revenue, transaction volume, cost-to-income ratio
   - Monthly revenue trend chart
   - Product revenue distribution

2. **Product Line Performance**
   - Revenue by product (sortable table)
   - Transaction counts and averages
   - Product mix pie chart

3. **GL Reconciliation Center**
   - Match rate gauge
   - Exception breakdown by type
   - Severity distribution

4. **Exception Drilldown**
   - Interactive filters (severity, type, date)
   - Sortable exception table
   - CSV export button

5. **Data Quality Report**
   - Row count summary
   - Validation status checks
   - Pipeline metadata

---

## Troubleshooting

### Streamlit not found
```bash
pip install streamlit
```

### Database connection error
```
Error: could not connect to server
```

**Fix**:
1. Ensure PostgreSQL is running
2. Set DATABASE_URL environment variable
3. Check credentials in `.env`
4. Initialize database: `python -m pipelines.init_database`

### Import errors
```
ModuleNotFoundError: No module named 'app'
```

**Fix**:
- Must run from project root: `cd C:\Users\abhij\banking-gl-reconciliation-dashboard`
- Use `streamlit run streamlit_app.py` (not `streamlit run app/dashboard/main.py`)

### Blank pages / no data showing
- Database empty (run ETL): `python -m pipelines.etl_main`
- Database not connected (check DATABASE_URL)
- Check Streamlit error details (enable in .streamlit/config.toml)

### Port 8501 already in use
```bash
streamlit run streamlit_app.py --server.port 8502
```

---

## Development

### Code Location
- Dashboard UI: `app/dashboard/main.py`
- Database models: `app/core/models.py`
- Database connection: `app/core/database.py`
- Root entry point: `streamlit_app.py`

### Adding Pages
Edit `app/dashboard/main.py`:
1. Create new function `def page_name():`
2. Add to `page = st.sidebar.radio()` options
3. Add to main() if/elif block

### Styling
- Theme: `.streamlit/config.toml`
- Custom CSS: In `app/dashboard/main.py` (st.markdown with style)

---

## Deployment

### Streamlit Cloud
```bash
git push  # Push to GitHub
# Go to https://share.streamlit.io
# Connect repo, select streamlit_app.py
# Deploy
```

### Docker
```bash
docker compose up dashboard
# Dashboard: http://localhost:8501
```

### Render/Railway
Use `DEPLOYMENT.md` for cloud setup.

---

## Verify Setup

Quick test:
```bash
# From project root
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from app.core.models import Transaction
print('Setup OK - Ready to run streamlit')
"
```

Then:
```bash
streamlit run streamlit_app.py
```

---

**Dashboard Ready**: http://localhost:8501
