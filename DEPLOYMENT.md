# Deployment Guide

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Docker (optional but recommended)

### Without Docker

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://postgres:password@localhost:5432/banking_db
export NUM_CUSTOMERS=5000
export NUM_ACCOUNTS=8000

# Initialize database
createdb banking_db
python -m pipelines.init_database

# Generate synthetic data
python -m pipelines.generate_synthetic_data

# Run ETL
python -m pipelines.etl_main

# Run tests
pytest -v

# Start services in different terminals
uvicorn app.api.main:app --reload
streamlit run app/dashboard/main.py
```

### With Docker Compose

```bash
# Build images
docker compose build

# Start all services
docker compose up

# View logs
docker compose logs -f

# Run tests
docker compose exec app pytest -v

# Stop services
docker compose down

# Clean up volumes
docker compose down -v
```

## Cloud Deployment

### 1. Streamlit Cloud (Dashboard)

**Easiest option** - Free tier available, works without PostgreSQL

#### 🚀 Streamlit Cloud with SQLite (No Database Setup)

**Recommended approach** - Works on free tier with local SQLite cache:

**Steps**:

1. Pre-generate synthetic data locally and commit to repo:
   ```bash
   python -m pipelines.generate_synthetic_data
   git add data/raw/*.csv
   git commit -m "Add synthetic data for Streamlit Cloud"
   git push origin main
   ```

2. Go to https://share.streamlit.io
3. Click "Create app"
4. Connect your GitHub repo
5. Select:
   - Repo: `your-username/banking-gl-reconciliation-dashboard`
   - Branch: `main`
   - File path: `streamlit_app.py`

6. No secrets needed! Dashboard automatically:
   - Loads CSV files from `data/raw/`
   - Creates SQLite cache on first run
   - Shows "Using Local SQLite Cache" in sidebar

7. Deploy!

**Works on free tier**: Yes ✅
- No database setup required
- CSV data committed to repo
- SQLite created in ephemeral filesystem
- Fast cold starts

#### 🗄️ Streamlit Cloud with PostgreSQL (If Needed)

For production with live data:

1. Push code to GitHub
   ```bash
   git push origin main
   ```

2. Set up external PostgreSQL (e.g., Supabase free tier)

3. Go to https://share.streamlit.io
4. Click "Create app"
5. Select `streamlit_app.py` as main file
6. Set secrets in Streamlit settings:
   ```
   [database]
   url = "postgresql://user:pass@host:5432/banking_db"
   ```

7. Dashboard auto-detects PostgreSQL and uses it

**Limitations**:
- Supabase free tier: Limited storage, no backups
- Recommended: Supabase Pro ($25/month) for production

---

### 2. Render (API + Database)

**Full-stack option** - Easiest for production

**Steps**:

1. Sign up at https://render.com
2. Connect GitHub
3. Create new "Web Service"
   - Select your repo
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`

4. Create PostgreSQL database:
   - New → PostgreSQL
   - Name: `banking_db`
   - Database: `banking_db`
   - User: `postgres`

5. Set environment variables:
   ```
   DATABASE_URL = postgresql://postgres:password@host:5432/banking_db
   NUM_CUSTOMERS = 5000
   NUM_ACCOUNTS = 8000
   SEED = 42
   ```

6. Create second Web Service for dashboard:
   - Start command: `streamlit run app/dashboard/main.py --server.port=$PORT`
   - Same DATABASE_URL

7. Deploy from git or use Render CLI

**Costs** (Pay-as-you-go):
- Web Service: ~$7/month
- PostgreSQL: ~$15/month
- Total: ~$22/month

---

### 3. Railway (Alternative)

**Modern, developer-friendly**

**Steps**:

1. Sign up at https://railway.app
2. New project → GitHub repo
3. Select `Dockerfile`
4. Add PostgreSQL service
5. Set environment variables
6. Deploy

**Costs**: Similar to Render

---

### 4. AWS (Enterprise)

**For larger deployments**

```bash
# ECR (Docker registry)
aws ecr create-repository --repository-name banking-dashboard

# ECS (Container service)
aws ecs create-cluster --cluster-name banking
aws ecs register-task-definition --cli-input-json file://task-def.json

# RDS (PostgreSQL)
aws rds create-db-instance \
  --db-instance-identifier banking-db \
  --engine postgres \
  --db-instance-class db.t3.micro

# ALB (Load balancer)
aws elbv2 create-load-balancer --name banking-alb

# Auto Scaling Group (optional)
aws autoscaling create-auto-scaling-group --cli-input-json file://asg.json
```

---

## Environment Variables

Create `.env` file locally:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/banking_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=banking_db
DB_USER=postgres
DB_PASSWORD=password

# Data Generation
NUM_CUSTOMERS=25000
NUM_ACCOUNTS=40000
NUM_TRANSACTIONS=500000
NUM_GL_ENTRIES=500000
DATA_MONTHS=12
SEED=42

# API
API_HOST=0.0.0.0
API_PORT=8000
API_ENV=production

# Logging
LOG_LEVEL=INFO
```

**In cloud platforms**, set these in the dashboard (NOT in code).

---

## GitHub Actions CI/CD

Pipeline automatically runs on push to main/develop:

1. **Tests** - Run pytest suite
2. **Linting** - Ruff, Black, MyPy
3. **Docker Build** - Verify image builds
4. **Security** - Bandit, Safety

View results at: `https://github.com/your-username/banking-gl-reconciliation-dashboard/actions`

---

## Database Initialization

**Automatic** (on first run):
```bash
python -m pipelines.init_database
```

**Manual**:
```bash
psql -U postgres -d banking_db -f sql/ddl/schema.sql
```

**Reset** (warning: deletes all data):
```bash
python -m pipelines.init_database --reset
```

---

## Scaling Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| **Database** | Vertical scaling (larger RDS instance) |
| **ETL** | Batch processing (Airflow, Prefect) |
| **API** | Horizontal (multiple pods, load balancer) |
| **Dashboard** | CDN caching + read replicas |

---

## Monitoring & Logging

### Local
```bash
make test
make validate
docker compose logs -f
```

### Cloud
- **Render**: https://dashboard.render.com → Logs tab
- **Streamlit**: https://share.streamlit.io → Manage app → Logs
- **AWS CloudWatch**: aws logs tail /aws/ecs/banking

---

## Troubleshooting

**Can't connect to database**
```bash
psql postgresql://postgres:password@localhost:5432/banking_db
```

**API not starting**
```bash
uvicorn app.api.main:app --reload --log-level debug
```

**Streamlit crashes**
```bash
streamlit run app/dashboard/main.py --logger.level=debug
```

**Data generation too slow**
```bash
# Reduce row counts in .env
NUM_TRANSACTIONS=50000  # Instead of 500000
```

---

## Security Checklist

- [ ] Database credentials in env variables, NOT in code
- [ ] HTTPS enabled (automatic on Render/Streamlit Cloud)
- [ ] API key authentication (if needed)
- [ ] SQL injection protection (SQLAlchemy ORM)
- [ ] CORS properly configured
- [ ] Secrets rotated quarterly
- [ ] Audit logging enabled
- [ ] Backups configured (RDS auto-backups)

---

## Cost Optimization

| Level | Solution |
|-------|----------|
| **Free** | Streamlit Cloud (small dataset) |
| **$5-10/mo** | Render + free PostgreSQL tier |
| **$20-50/mo** | Render + managed PostgreSQL |
| **$100+/mo** | AWS + auto-scaling |

**Recommendation**: Start with Render free tier, upgrade as needed.

---

## Next Steps

1. ✅ Local testing (`make test`)
2. ✅ Docker validation (`docker compose up`)
3. → Deploy to Streamlit Cloud (dashboard)
4. → Deploy to Render (API)
5. → Monitor and optimize

**Questions?** See [README.md](README.md) or check [GitHub Issues](https://github.com/your-username/banking-gl-reconciliation-dashboard/issues)
