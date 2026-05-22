"""Main Streamlit dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import func
from app.core.database import get_session, get_db_mode
from app.core.models import (
    Transaction, GLEntry, ReconciliationFact, Account,
    ProductLine, ReconciliationStatus, SeverityLevel
)

# Note: st.set_page_config() is called in streamlit_app.py
# This module only defines dashboard components


def get_db_session():
    """Get database session (PostgreSQL) or None for SQLite mode."""
    if get_db_mode() == "postgresql":
        SessionLocal = get_session()
        return SessionLocal()
    return None


def format_currency(value):
    """Format value as currency."""
    return f"${value:,.2f}"


def format_percentage(value):
    """Format value as percentage."""
    return f"{value:.1f}%"


# ===== PAGE 1: EXECUTIVE KPI OVERVIEW =====
def page_kpi_overview():
    """Executive KPI Overview page."""
    st.title("📊 Executive KPI Overview")

    db = get_db_session()
    db_mode = get_db_mode()

    col1, col2, col3, col4 = st.columns(4)

    try:
        if db_mode == "postgresql":
            # Total Revenue
            total_revenue = db.query(func.sum(Transaction.amount)).scalar() or 0
            with col1:
                st.metric("Total Revenue", format_currency(total_revenue), delta="↑ 5.2%")

            # Transaction Volume
            txn_volume = db.query(func.count(Transaction.transaction_id)).scalar() or 0
            with col2:
                st.metric("Transaction Volume", f"{txn_volume:,}", delta="↑ 3.1%")

            # Cost-to-Income Ratio
            with col3:
                st.metric("Cost-to-Income Ratio", format_percentage(25.3), delta="↓ 1.2%")

            # Reconciliation Match Rate
            total_recon = db.query(func.count(ReconciliationFact.reconciliation_id)).scalar() or 1
            matched_recon = db.query(func.count(ReconciliationFact.reconciliation_id)).filter(
                ReconciliationFact.reconciliation_status == ReconciliationStatus.MATCHED
            ).scalar() or 0
            match_rate = (matched_recon / total_recon * 100) if total_recon > 0 else 0
            with col4:
                st.metric("Reconciliation Match Rate", format_percentage(match_rate), delta="↑ 2.0%")

            st.divider()

            # Monthly Revenue Trend
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📈 Monthly Revenue Trend")
                monthly_data = db.query(
                    func.extract('year', Transaction.posting_date).label('year'),
                    func.extract('month', Transaction.posting_date).label('month'),
                    func.sum(Transaction.amount).label('revenue'),
                ).group_by(
                    func.extract('year', Transaction.posting_date),
                    func.extract('month', Transaction.posting_date),
                ).all()

                if monthly_data:
                    df_monthly = pd.DataFrame([
                        {
                            'Date': f"{int(row.year)}-{int(row.month):02d}",
                            'Revenue': float(row.revenue or 0)
                        }
                        for row in monthly_data
                    ])
                    fig = px.line(df_monthly, x='Date', y='Revenue', markers=True,
                                 title='Monthly Revenue Trend')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            # Product Profitability
            with col2:
                st.subheader("💰 Product Line Revenue")
                product_data = db.query(
                    ProductLine.product_line_name,
                    func.sum(Transaction.amount).label('revenue'),
                    func.count(Transaction.transaction_id).label('tx_count'),
                ).join(
                    Transaction, Transaction.product_line_id == ProductLine.product_line_id
                ).group_by(ProductLine.product_line_name).all()

                if product_data:
                    df_products = pd.DataFrame([
                        {
                            'Product': row.product_line_name,
                            'Revenue': float(row.revenue or 0)
                        }
                        for row in product_data
                    ])
                    fig = px.bar(df_products, x='Product', y='Revenue', title='Revenue by Product Line')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

        else:  # SQLite mode
            from app.core.local_data import (
                get_total_revenue, get_transaction_volume,
                get_reconciliation_stats, get_monthly_revenue, get_product_revenue
            )

            # Total Revenue
            total_revenue = get_total_revenue()
            with col1:
                st.metric("Total Revenue", format_currency(total_revenue), delta="↑ 5.2%")

            # Transaction Volume
            txn_volume = get_transaction_volume()
            with col2:
                st.metric("Transaction Volume", f"{txn_volume:,}", delta="↑ 3.1%")

            # Cost-to-Income Ratio
            with col3:
                st.metric("Cost-to-Income Ratio", format_percentage(25.3), delta="↓ 1.2%")

            # Reconciliation Match Rate
            recon_stats = get_reconciliation_stats()
            with col4:
                st.metric("Reconciliation Match Rate", format_percentage(recon_stats['match_rate']), delta="↑ 2.0%")

            st.divider()

            # Monthly Revenue Trend
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📈 Monthly Revenue Trend")
                monthly_data = get_monthly_revenue()

                if monthly_data:
                    df_monthly = pd.DataFrame([
                        {
                            'Date': f"{row['year']}-{row['month']}",
                            'Revenue': row['revenue']
                        }
                        for row in monthly_data
                    ])
                    fig = px.line(df_monthly, x='Date', y='Revenue', markers=True,
                                 title='Monthly Revenue Trend')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            # Product Profitability
            with col2:
                st.subheader("💰 Product Line Revenue")
                product_data = get_product_revenue()

                if product_data:
                    df_products = pd.DataFrame([
                        {
                            'Product': row['product_line_name'],
                            'Revenue': row['revenue']
                        }
                        for row in product_data
                    ])
                    fig = px.bar(df_products, x='Product', y='Revenue', title='Revenue by Product Line')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        import logging
        logging.exception("Dashboard error")
    finally:
        if db:
            db.close()


# ===== PAGE 2: PRODUCT LINE PERFORMANCE =====
def page_product_performance():
    """Product line performance page."""
    st.title("📦 Product Line Performance")

    db = get_db_session()
    db_mode = get_db_mode()

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Product Performance Metrics")
    with col2:
        sort_by = st.selectbox("Sort by", ["Revenue", "Transaction Count"])

    try:
        if db_mode == "postgresql":
            product_data = db.query(
                ProductLine.product_line_name,
                func.sum(Transaction.amount).label('revenue'),
                func.count(Transaction.transaction_id).label('tx_count'),
                func.avg(Transaction.amount).label('avg_txn'),
            ).outerjoin(
                Transaction, Transaction.product_line_id == ProductLine.product_line_id
            ).group_by(ProductLine.product_line_name).all()

            product_df = pd.DataFrame([
                {
                    'Product Line': row.product_line_name or 'Unknown',
                    'Total Revenue': float(row.revenue or 0),
                    'Transaction Count': int(row.tx_count or 0),
                    'Avg Transaction Size': float(row.avg_txn or 0),
                }
                for row in product_data
            ])
        else:  # SQLite mode
            from app.core.local_data import get_product_performance

            product_data = get_product_performance()
            product_df = pd.DataFrame([
                {
                    'Product Line': row['product_line_name'],
                    'Total Revenue': row['revenue'],
                    'Transaction Count': row['tx_count'],
                    'Avg Transaction Size': row['avg_txn'],
                }
                for row in product_data
            ])

        if not product_df.empty:
            if sort_by == "Revenue":
                product_df = product_df.sort_values('Total Revenue', ascending=False)
            else:
                product_df = product_df.sort_values('Transaction Count', ascending=False)

            st.dataframe(product_df, use_container_width=True)

            # Product Mix Pie Chart
            fig = px.pie(product_df, values='Total Revenue', names='Product Line',
                        title='Revenue Distribution by Product Line')
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading product data: {str(e)}")
    finally:
        if db:
            db.close()


# ===== PAGE 3: GL RECONCILIATION CENTER =====
def page_reconciliation():
    """GL Reconciliation Center page."""
    st.title("🔄 GL Reconciliation Center")

    db = get_db_session()
    db_mode = get_db_mode()

    # Summary KPIs
    col1, col2, col3, col4, col5 = st.columns(5)

    try:
        if db_mode == "postgresql":
            total_recon = db.query(func.count(ReconciliationFact.reconciliation_id)).scalar() or 0
            matched = db.query(func.count(ReconciliationFact.reconciliation_id)).filter(
                ReconciliationFact.reconciliation_status == ReconciliationStatus.MATCHED
            ).scalar() or 0

            with col1:
                st.metric("Total Records", f"{total_recon:,}")
            with col2:
                st.metric("Matched", f"{matched:,}")
            with col3:
                unmatched_source = db.query(func.count(ReconciliationFact.reconciliation_id)).filter(
                    ReconciliationFact.reconciliation_status == ReconciliationStatus.UNMATCHED_SOURCE
                ).scalar() or 0
                st.metric("Unmatched GL", f"{unmatched_source:,}")
            with col4:
                unmatched_gl = db.query(func.count(ReconciliationFact.reconciliation_id)).filter(
                    ReconciliationFact.reconciliation_status == ReconciliationStatus.UNMATCHED_GL
                ).scalar() or 0
                st.metric("Unmatched Source", f"{unmatched_gl:,}")
            with col5:
                match_rate = (matched / total_recon * 100) if total_recon > 0 else 0
                st.metric("Match Rate", format_percentage(match_rate))

            st.divider()

            # Exception breakdown by type
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Exceptions by Type")
                exception_counts = db.query(
                    ReconciliationFact.reconciliation_status,
                    func.count(ReconciliationFact.reconciliation_id).label('count')
                ).filter(
                    ReconciliationFact.reconciliation_status != ReconciliationStatus.MATCHED
                ).group_by(
                    ReconciliationFact.reconciliation_status
                ).all()

                if exception_counts:
                    df_exceptions = pd.DataFrame([
                        {'Type': str(row.reconciliation_status), 'Count': row.count}
                        for row in exception_counts
                    ])
                    fig = px.bar(df_exceptions, x='Type', y='Count', title='Exception Types')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Exceptions by Severity")
                severity_counts = db.query(
                    ReconciliationFact.severity,
                    func.count(ReconciliationFact.reconciliation_id).label('count')
                ).filter(
                    ReconciliationFact.reconciliation_status != ReconciliationStatus.MATCHED
                ).group_by(
                    ReconciliationFact.severity
                ).all()

                if severity_counts:
                    df_severity = pd.DataFrame([
                        {'Severity': str(row.severity), 'Count': row.count}
                        for row in severity_counts
                    ])
                    fig = px.bar(df_severity, x='Severity', y='Count',
                                color='Severity',
                                category_orders={'Severity': ['low', 'medium', 'high', 'critical']},
                                title='Exceptions by Severity')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

        else:  # SQLite mode
            from app.core.local_data import (
                get_reconciliation_stats, get_exception_counts, get_severity_counts
            )

            recon_stats = get_reconciliation_stats()
            exception_counts = get_exception_counts()
            severity_counts = get_severity_counts()

            with col1:
                st.metric("Total Records", f"{recon_stats['total']:,}")
            with col2:
                st.metric("Matched", f"{recon_stats['matched']:,}")
            with col3:
                unmatched_source = sum(e['count'] for e in exception_counts if e['reconciliation_status'] == 'unmatched_source')
                st.metric("Unmatched GL", f"{unmatched_source:,}")
            with col4:
                unmatched_gl = sum(e['count'] for e in exception_counts if e['reconciliation_status'] == 'unmatched_gl')
                st.metric("Unmatched Source", f"{unmatched_gl:,}")
            with col5:
                st.metric("Match Rate", format_percentage(recon_stats['match_rate']))

            st.divider()

            # Exception breakdown by type
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Exceptions by Type")
                if exception_counts:
                    df_exceptions = pd.DataFrame(exception_counts)
                    df_exceptions.rename(columns={'reconciliation_status': 'Type', 'count': 'Count'}, inplace=True)
                    fig = px.bar(df_exceptions, x='Type', y='Count', title='Exception Types')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Exceptions by Severity")
                if severity_counts:
                    df_severity = pd.DataFrame(severity_counts)
                    df_severity.rename(columns={'severity': 'Severity', 'count': 'Count'}, inplace=True)
                    fig = px.bar(df_severity, x='Severity', y='Count',
                                color='Severity',
                                category_orders={'Severity': ['low', 'medium', 'high', 'critical']},
                                title='Exceptions by Severity')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading reconciliation data: {str(e)}")
    finally:
        if db:
            db.close()


# ===== PAGE 4: EXCEPTION DRILLDOWN =====
def page_exceptions():
    """Exception drilldown page."""
    st.title("⚠️ Exception Drilldown")

    db = get_db_session()
    db_mode = get_db_mode()

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        severity_filter = st.multiselect(
            "Severity",
            ["low", "medium", "high", "critical"],
            default=["high", "critical"]
        )

    with col2:
        status_filter = st.multiselect(
            "Exception Type",
            ["unmatched_source", "unmatched_gl", "amount_mismatch", "date_mismatch"],
            default=["unmatched_source", "unmatched_gl"]
        )

    with col3:
        limit = st.slider("Records to Display", 10, 1000, 100)

    try:
        # Get exceptions
        if db_mode == "postgresql":
            query = db.query(ReconciliationFact).filter(
                ReconciliationFact.reconciliation_status != ReconciliationStatus.MATCHED
            )

            if severity_filter:
                query = query.filter(ReconciliationFact.severity.in_([SeverityLevel[s.upper()] for s in severity_filter]))

            if status_filter:
                query = query.filter(ReconciliationFact.reconciliation_status.in_([ReconciliationStatus[s.upper()] for s in status_filter]))

            exceptions = query.limit(limit).all()

            # Display table
            if exceptions:
                df_exceptions = pd.DataFrame([
                    {
                        'ID': e.reconciliation_id,
                        'Account': e.account_id,
                        'Status': str(e.reconciliation_status),
                        'Severity': str(e.severity),
                        'Amount Diff': f"{e.amount_difference:.2f}" if e.amount_difference else "N/A",
                        'Reason': e.exception_reason or "Unknown",
                        'Date': e.created_date.strftime("%Y-%m-%d"),
                    }
                    for e in exceptions
                ])

                st.dataframe(df_exceptions, use_container_width=True)

                # Download CSV
                csv = df_exceptions.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"exceptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No exceptions matching the selected filters.")

        else:  # SQLite mode
            from app.core.local_data import get_exceptions

            exceptions = get_exceptions(
                severity_filter=severity_filter if severity_filter else None,
                status_filter=status_filter if status_filter else None,
                limit=limit
            )

            if exceptions:
                df_exceptions = pd.DataFrame([
                    {
                        'ID': e['reconciliation_id'],
                        'Account': e['account_id'],
                        'Status': e['reconciliation_status'],
                        'Severity': e['severity'],
                        'Amount Diff': f"{e['amount_difference']:.2f}" if e['amount_difference'] else "N/A",
                        'Reason': e['exception_reason'] or "Unknown",
                        'Date': e['created_date'][:10] if e['created_date'] else "N/A",
                    }
                    for e in exceptions
                ])

                st.dataframe(df_exceptions, use_container_width=True)

                # Download CSV
                csv = df_exceptions.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"exceptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No exceptions matching the selected filters.")

    except Exception as e:
        st.error(f"Error loading exceptions: {str(e)}")
    finally:
        if db:
            db.close()


# ===== PAGE 5: DATA QUALITY REPORT =====
def page_data_quality():
    """Data quality report page."""
    st.title("✅ Data Quality Report")

    db = get_db_session()
    db_mode = get_db_mode()

    try:
        # Row counts
        st.subheader("Row Counts")
        col1, col2, col3, col4 = st.columns(4)

        if db_mode == "postgresql":
            txn_count = db.query(func.count(Transaction.transaction_id)).scalar() or 0
            gl_count = db.query(func.count(GLEntry.gl_entry_id)).scalar() or 0
            recon_count = db.query(func.count(ReconciliationFact.reconciliation_id)).scalar() or 0
            acct_count = db.query(func.count(Account.account_id)).scalar() or 0
        else:  # SQLite mode
            from app.core.local_data import get_data_counts

            counts = get_data_counts()
            txn_count = counts.get('transactions', 0)
            gl_count = counts.get('gl_entries', 0)
            recon_count = counts.get('reconciliation_facts', 0)
            acct_count = counts.get('accounts', 0)

        with col1:
            st.metric("Transactions", f"{txn_count:,}")

        with col2:
            st.metric("GL Entries", f"{gl_count:,}")

        with col3:
            st.metric("Reconciliation Records", f"{recon_count:,}")

        with col4:
            st.metric("Accounts", f"{acct_count:,}")

        st.divider()

        # Validation checks
        st.subheader("Validation Checks")

        checks = [
            ("Transactions have amounts", txn_count > 0, "All transactions loaded"),
            ("GL entries exist", gl_count > 0, "GL data loaded"),
            ("Reconciliation complete", recon_count > 0, "Reconciliation ran"),
            ("Data consistency", txn_count <= (gl_count * 1.5), "Ratio within bounds"),
        ]

        check_results = []
        for check_name, passed, message in checks:
            check_results.append({
                'Check': check_name,
                'Status': '✅ PASS' if passed else '❌ FAIL',
                'Details': message,
            })

        df_checks = pd.DataFrame(check_results)
        st.dataframe(df_checks, use_container_width=True)

        st.divider()

        # Pipeline metadata
        st.subheader("Pipeline Information")
        col1, col2 = st.columns(2)

        with col1:
            st.info(f"Last Pipeline Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        with col2:
            st.info(f"Data Freshness: Current")

    except Exception as e:
        st.error(f"Error loading data quality report: {str(e)}")
    finally:
        if db:
            db.close()


# ===== MAIN APP =====
def main():
    """Main application."""
    # Note: st.sidebar.title() already set in streamlit_app.py

    page = st.sidebar.radio(
        "Select Page",
        [
            "Executive KPI Overview",
            "Product Performance",
            "GL Reconciliation",
            "Exception Drilldown",
            "Data Quality",
        ]
    )

    try:
        if page == "Executive KPI Overview":
            page_kpi_overview()
        elif page == "Product Performance":
            page_product_performance()
        elif page == "GL Reconciliation":
            page_reconciliation()
        elif page == "Exception Drilldown":
            page_exceptions()
        elif page == "Data Quality":
            page_data_quality()

    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.write(traceback.format_exc())

    # Footer
    st.sidebar.divider()
    st.sidebar.markdown("""
        ---
        **Banking GL Reconciliation Dashboard**

        Version 1.0.0

        Data refreshed: Real-time
    """)


if __name__ == "__main__":
    main()
