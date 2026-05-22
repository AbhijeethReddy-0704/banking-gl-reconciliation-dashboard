"""Verify dashboard setup without running Streamlit UI."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

print("=" * 70)
print("BANKING DASHBOARD SETUP VERIFICATION")
print("=" * 70)

# Step 1: Test imports
print("\n[1] Testing imports...")
try:
    from app.core.database import get_db_mode, init_db, get_engine
    from app.core.local_data import (
        ensure_data_available,
        get_total_revenue,
        get_transaction_volume,
        get_reconciliation_stats,
        get_monthly_revenue,
        get_product_revenue,
    )
    from app.dashboard.main import main
    print("    OK - All imports successful")
except Exception as e:
    print(f"    FAIL - Import error: {e}")
    sys.exit(1)

# Step 2: Initialize database
print("\n[2] Initializing database...")
try:
    ensure_data_available()
    init_db()
    db_mode = get_db_mode()
    print(f"    OK - Database mode: {db_mode}")
except Exception as e:
    print(f"    FAIL - Database error: {e}")
    sys.exit(1)

# Step 3: Test data access (SQLite mode)
print("\n[3] Testing data access...")
try:
    if db_mode == "sqlite":
        total_revenue = get_total_revenue()
        txn_volume = get_transaction_volume()
        recon_stats = get_reconciliation_stats()
        monthly_data = get_monthly_revenue()
        product_data = get_product_revenue()

        print(f"    Total Revenue: ${total_revenue:,.2f}")
        print(f"    Transaction Volume: {txn_volume:,}")
        print(f"    Reconciliation Match Rate: {recon_stats['match_rate']:.1f}%")
        print(f"    Monthly Data Points: {len(monthly_data)}")
        print(f"    Product Lines: {len(product_data)}")
        print("    OK - Data access working")
    else:
        print("    OK - PostgreSQL mode detected")
except Exception as e:
    print(f"    FAIL - Data access error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Test dashboard main function exists
print("\n[4] Testing dashboard module...")
try:
    from app.dashboard.main import (
        get_db_session,
        page_kpi_overview,
        page_product_performance,
        page_reconciliation,
        page_exceptions,
        page_data_quality,
    )
    print("    OK - Dashboard pages available")
except Exception as e:
    print(f"    FAIL - Dashboard error: {e}")
    sys.exit(1)

# Step 5: Check data files
print("\n[5] Checking data files...")
try:
    from app.core.local_data import DATA_DIR, RAW_DIR, CACHE_DB

    csv_files = list(RAW_DIR.glob("*.csv"))
    print(f"    CSV files in {RAW_DIR}: {len(csv_files)}")
    if csv_files:
        for csv in sorted(csv_files):
            print(f"      - {csv.name}")

    if CACHE_DB.exists():
        cache_size_mb = CACHE_DB.stat().st_size / (1024 * 1024)
        print(f"    SQLite cache: {CACHE_DB.name} ({cache_size_mb:.1f} MB)")
    else:
        print(f"    SQLite cache: Will be created on first Streamlit run")

    print("    OK - Data files in place")
except Exception as e:
    print(f"    FAIL - Data file error: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("VERIFICATION COMPLETE - Dashboard Ready!")
print("=" * 70)
print("\nTo start the dashboard, run:")
print("  streamlit run streamlit_app.py")
print("\nThen visit: http://localhost:8501")
print("\n" + "=" * 70)
