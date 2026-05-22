-- Banking GL Reconciliation Database Schema
-- This file documents the DDL used by SQLAlchemy ORM models

-- Customers dimension
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_type VARCHAR(50) NOT NULL,
    industry VARCHAR(100),
    country VARCHAR(100) NOT NULL,
    risk_segment VARCHAR(50),
    created_date DATE NOT NULL,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Branches dimension
CREATE TABLE IF NOT EXISTS branches (
    branch_id SERIAL PRIMARY KEY,
    branch_name VARCHAR(255) NOT NULL,
    branch_code VARCHAR(10) UNIQUE NOT NULL,
    country VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    created_date DATE NOT NULL
);

-- Employees dimension
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    employee_name VARCHAR(255) NOT NULL,
    branch_id INTEGER REFERENCES branches(branch_id),
    role VARCHAR(100),
    hire_date DATE NOT NULL
);

-- Product lines dimension
CREATE TABLE IF NOT EXISTS product_lines (
    product_line_id SERIAL PRIMARY KEY,
    product_line_name VARCHAR(100) UNIQUE NOT NULL,
    product_code VARCHAR(20) UNIQUE NOT NULL,
    category VARCHAR(50),
    created_date DATE NOT NULL
);

-- Accounts dimension
CREATE TABLE IF NOT EXISTS accounts (
    account_id SERIAL PRIMARY KEY,
    account_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
    product_line_id INTEGER REFERENCES product_lines(product_line_id),
    account_type VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'USD',
    balance DECIMAL(18,2) DEFAULT 0,
    opened_date DATE NOT NULL,
    closed_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Transactions fact table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    product_line_id INTEGER REFERENCES product_lines(product_line_id),
    branch_id INTEGER REFERENCES branches(branch_id),
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    posting_date DATE NOT NULL,
    value_date DATE,
    description VARCHAR(500),
    reference VARCHAR(100),
    employee_id INTEGER REFERENCES employees(employee_id),
    created_date TIMESTAMP NOT NULL
);

-- GL entries fact table
CREATE TABLE IF NOT EXISTS gl_entries (
    gl_entry_id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES transactions(transaction_id),
    account_id INTEGER REFERENCES accounts(account_id),
    gl_account_code VARCHAR(20) NOT NULL,
    gl_account_name VARCHAR(255),
    product_line_id INTEGER REFERENCES product_lines(product_line_id),
    debit_amount DECIMAL(18,2) DEFAULT 0,
    credit_amount DECIMAL(18,2) DEFAULT 0,
    posting_date DATE NOT NULL,
    value_date DATE,
    currency VARCHAR(3) DEFAULT 'USD',
    journal_reference VARCHAR(50),
    created_date TIMESTAMP NOT NULL
);

-- Reconciliation facts
CREATE TABLE IF NOT EXISTS reconciliation_facts (
    reconciliation_id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES transactions(transaction_id),
    gl_entry_id INTEGER REFERENCES gl_entries(gl_entry_id),
    account_id INTEGER REFERENCES accounts(account_id),
    product_line_id INTEGER REFERENCES product_lines(product_line_id),
    reconciliation_status VARCHAR(50) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    source_amount DECIMAL(18,2),
    gl_amount DECIMAL(18,2),
    amount_difference DECIMAL(18,2),
    source_date DATE,
    gl_date DATE,
    date_difference_days INTEGER,
    match_confidence FLOAT DEFAULT 1.0,
    exception_reason VARCHAR(500),
    resolved_date TIMESTAMP,
    resolved_by VARCHAR(255),
    created_date TIMESTAMP NOT NULL
);

-- Calendar dimension
CREATE TABLE IF NOT EXISTS calendar (
    date_id SERIAL PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    week_of_year INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT FALSE
);

-- Data quality metrics
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    metric_id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    row_count INTEGER,
    null_count INTEGER,
    null_percentage FLOAT,
    duplicate_rows INTEGER,
    validation_status VARCHAR(50),
    check_timestamp TIMESTAMP NOT NULL
);

-- Pipeline runs
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id SERIAL PRIMARY KEY,
    run_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    rows_processed INTEGER,
    rows_failed INTEGER,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds FLOAT,
    error_message VARCHAR(1000)
);

-- Create indexes
CREATE INDEX idx_customer_type ON customers(customer_type);
CREATE INDEX idx_branch_code ON branches(branch_code);
CREATE INDEX idx_account_number ON accounts(account_number);
CREATE INDEX idx_account_customer ON accounts(customer_id);
CREATE INDEX idx_transaction_account ON transactions(account_id);
CREATE INDEX idx_transaction_date ON transactions(posting_date);
CREATE INDEX idx_gl_account ON gl_entries(gl_account_code);
CREATE INDEX idx_gl_date ON gl_entries(posting_date);
CREATE INDEX idx_reconciliation_status ON reconciliation_facts(reconciliation_status);
CREATE INDEX idx_reconciliation_severity ON reconciliation_facts(severity);
CREATE INDEX idx_calendar_date ON calendar(full_date);
