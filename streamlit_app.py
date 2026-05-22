"""Root-level Streamlit app entry point.

Run from project root:
    streamlit run streamlit_app.py
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Set up environment
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "false")
os.environ.setdefault("LOG_LEVEL", "INFO")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# MUST be first Streamlit command (before any other st.* calls)
import streamlit as st
st.set_page_config(
    page_title="Banking GL Reconciliation Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: bold;
        color: #0066cc;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_app():
    """Initialize app on first run."""
    from app.core.database import get_db_mode, init_db
    from app.core.local_data import ensure_data_available

    # Ensure local data available first
    ensure_data_available()

    # Initialize database (handles PostgreSQL or SQLite)
    init_db()

    # Get database mode
    db_mode = get_db_mode()
    return db_mode


# Initialize on startup
db_mode = init_app()

# Show connection status in sidebar
with st.sidebar:
    st.title("Banking Dashboard")
    if db_mode == "postgresql":
        st.success("✓ Connected to PostgreSQL", icon="🗄️")
    else:
        st.info("📦 Using Local SQLite Cache", icon="ℹ️")

# Import and run dashboard (now safe - set_page_config already called)
from app.dashboard.main import main

if __name__ == "__main__":
    main()
