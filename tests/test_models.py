"""Tests for ORM models."""

import pytest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.models import (
    Base, Customer, Branch, Account, Transaction,
    GLEntry, ProductLine, ReconciliationFact,
    ReconciliationStatus, SeverityLevel
)


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_customer_creation(db_session):
    """Test customer creation."""
    customer = Customer(
        customer_id=1,
        customer_name="Test Customer",
        customer_type="retail",
        industry="Finance",
        country="US",
        risk_segment="Low Risk",
        created_date=date.today(),
    )
    db_session.add(customer)
    db_session.commit()

    result = db_session.query(Customer).filter_by(customer_id=1).first()
    assert result.customer_name == "Test Customer"
    assert result.risk_segment == "Low Risk"


def test_branch_creation(db_session):
    """Test branch creation."""
    branch = Branch(
        branch_id=1,
        branch_name="New York Branch",
        branch_code="BR0001",
        country="US",
        region="NY",
        created_date=date.today(),
    )
    db_session.add(branch)
    db_session.commit()

    result = db_session.query(Branch).filter_by(branch_code="BR0001").first()
    assert result.branch_name == "New York Branch"


def test_product_line_creation(db_session):
    """Test product line creation."""
    product = ProductLine(
        product_line_id=1,
        product_line_name="Credit Cards",
        product_code="CARDS",
        category="Cards",
        created_date=date.today(),
    )
    db_session.add(product)
    db_session.commit()

    result = db_session.query(ProductLine).filter_by(product_code="CARDS").first()
    assert result.product_line_name == "Credit Cards"


def test_account_creation(db_session):
    """Test account creation."""
    customer = Customer(
        customer_id=1,
        customer_name="Test",
        customer_type="retail",
        country="US",
        created_date=date.today(),
    )
    branch = Branch(
        branch_id=1,
        branch_name="Test Branch",
        branch_code="BR0001",
        country="US",
        created_date=date.today(),
    )
    product = ProductLine(
        product_line_id=1,
        product_line_name="Cards",
        product_code="CARDS",
        created_date=date.today(),
    )

    db_session.add_all([customer, branch, product])
    db_session.commit()

    account = Account(
        account_id=1,
        account_number="ACC0000000001",
        customer_id=1,
        branch_id=1,
        product_line_id=1,
        account_type="Checking",
        balance=5000.00,
        opened_date=date.today(),
    )
    db_session.add(account)
    db_session.commit()

    result = db_session.query(Account).filter_by(account_number="ACC0000000001").first()
    assert result.balance == 5000.00


def test_transaction_creation(db_session):
    """Test transaction creation."""
    # Setup
    customer = Customer(customer_id=1, customer_name="Test", customer_type="retail", country="US", created_date=date.today())
    branch = Branch(branch_id=1, branch_name="Test", branch_code="BR0001", country="US", created_date=date.today())
    product = ProductLine(product_line_id=1, product_line_name="Cards", product_code="CARDS", created_date=date.today())
    account = Account(account_id=1, account_number="ACC0000000001", customer_id=1, branch_id=1, product_line_id=1, opened_date=date.today())

    db_session.add_all([customer, branch, product, account])
    db_session.commit()

    # Create transaction
    transaction = Transaction(
        transaction_id=1,
        account_id=1,
        product_line_id=1,
        branch_id=1,
        transaction_type="debit",
        amount=100.00,
        posting_date=date.today(),
        created_date=datetime.now(),
    )
    db_session.add(transaction)
    db_session.commit()

    result = db_session.query(Transaction).filter_by(transaction_id=1).first()
    assert result.amount == 100.00
    assert result.transaction_type == "debit"


def test_reconciliation_fact_creation(db_session):
    """Test reconciliation fact creation."""
    recon = ReconciliationFact(
        reconciliation_id=1,
        account_id=1,
        reconciliation_status=ReconciliationStatus.MATCHED,
        severity=SeverityLevel.LOW,
        source_amount=100.00,
        gl_amount=100.00,
        match_confidence=1.0,
        created_date=datetime.now(),
    )
    db_session.add(recon)
    db_session.commit()

    result = db_session.query(ReconciliationFact).filter_by(reconciliation_id=1).first()
    assert result.reconciliation_status == ReconciliationStatus.MATCHED
    assert result.severity == SeverityLevel.LOW
