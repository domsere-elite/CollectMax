-- Enable UUID extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Ingest job tracking table
CREATE TABLE IF NOT EXISTS ingest_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id integer REFERENCES portfolios(id),
    filename text,
    file_path text,
    status varchar(50) DEFAULT 'queued',
    rows_processed integer DEFAULT 0,
    rows_failed integer DEFAULT 0,
    error_message text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    started_at timestamp with time zone,
    finished_at timestamp with time zone
);

CREATE INDEX IF NOT EXISTS idx_ingest_jobs_status ON ingest_jobs(status);

-- Idempotency: prevent duplicate debts per portfolio
CREATE UNIQUE INDEX IF NOT EXISTS debts_unique_portfolio_client_ref
    ON debts (portfolio_id, client_reference_number)
    WHERE client_reference_number IS NOT NULL;
