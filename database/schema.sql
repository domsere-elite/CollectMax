-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Clients Table
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sftp_folder_path VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Portfolios Table (Commissions)
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    name VARCHAR(255) NOT NULL,
    commission_percentage DECIMAL(5, 2) NOT NULL CHECK (commission_percentage >= 0 AND commission_percentage <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Debtors Table (PII & Deduplication)
CREATE TABLE debtors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ssn_hash VARCHAR(255) UNIQUE NOT NULL, -- Deduplication Key (SHA-256)
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    dob DATE, -- New: Identity Verification
    address_1 VARCHAR(255), -- New
    address_2 VARCHAR(255), -- New
    city VARCHAR(100), -- New
    state VARCHAR(2), -- New: Licensing Check
    zip_code VARCHAR(20), -- Timezone Calc
    phone VARCHAR(50), -- Primary Phone
    mobile_consent BOOLEAN DEFAULT FALSE, -- New: SMS Consent
    email VARCHAR(255),
    do_not_contact BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Debts Table
CREATE TYPE debt_status AS ENUM ('New', 'Paid', 'Closed', 'Payment Plan');

CREATE TABLE debts (
    id SERIAL PRIMARY KEY,
    debtor_id UUID REFERENCES debtors(id),
    portfolio_id INTEGER REFERENCES portfolios(id),
    client_reference_number VARCHAR(100), -- New
    original_account_number VARCHAR(100) NOT NULL,
    original_creditor VARCHAR(255), -- New
    date_opened DATE, -- New
    charge_off_date DATE, -- New: Anchor for Debt Age
    principal_balance DECIMAL(12, 2), -- New
    fees_costs DECIMAL(12, 2), -- New
    amount_due DECIMAL(12, 2) NOT NULL, -- "Total Placed"
    last_payment_date DATE, -- New: SOL Validation
    last_payment_amount DECIMAL(12, 2), -- New
    total_paid_amount DECIMAL(12, 2) DEFAULT 0.00,
    last_payment_id INTEGER,
    last_payment_reference VARCHAR(255),
    last_payment_method VARCHAR(50),
    status debt_status DEFAULT 'New',
    date_assigned TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Payments Table (Split Ledger)
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    debt_id INTEGER REFERENCES debts(id),
    amount_paid DECIMAL(12, 2) NOT NULL,
    agency_portion DECIMAL(12, 2) NOT NULL, -- Calculated
    client_portion DECIMAL(12, 2) NOT NULL, -- Calculated
    transaction_reference VARCHAR(255),
    scheduled_payment_id INTEGER,
    payment_method VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Payment Plans
CREATE TABLE payment_plans (
    id SERIAL PRIMARY KEY,
    debt_id INTEGER REFERENCES debts(id),
    total_settlement_amount DECIMAL(12, 2) NOT NULL,
    down_payment_amount DECIMAL(12, 2) DEFAULT 0.00,
    installment_count INTEGER NOT NULL,
    frequency VARCHAR(50) NOT NULL, -- 'weekly', 'bi-weekly', 'monthly'
    start_date DATE NOT NULL,
    card_token VARCHAR(255), -- USA ePay Card Reference Key
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'cancelled'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled Payments
CREATE TABLE scheduled_payments (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER REFERENCES payment_plans(id) ON DELETE CASCADE,
    amount DECIMAL(12, 2) NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'paid', 'missed', 'cancelled', 'declined'
    actual_payment_id INTEGER REFERENCES payments(id),
    processed_at TIMESTAMP WITH TIME ZONE,
    transaction_reference VARCHAR(255),
    payment_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Interaction Logs (Compliance)
CREATE TYPE action_type AS ENUM ('Call', 'Email', 'SMS', 'Other');

CREATE TABLE interaction_logs (
    id SERIAL PRIMARY KEY,
    debt_id INTEGER REFERENCES debts(id),
    agent_id VARCHAR(100), -- Reference to Auth User
    action_type action_type NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Index for 7-in-7 Rule
CREATE INDEX idx_interaction_logs_debt_id_timestamp ON interaction_logs(debt_id, timestamp);
