-- Add SendGrid email tracking tables and fields
ALTER TABLE debtors
    ADD COLUMN IF NOT EXISTS email_bounce_status VARCHAR(50),
    ADD COLUMN IF NOT EXISTS email_last_bounced_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS email_unsubscribed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_unsubscribed_at TIMESTAMP WITH TIME ZONE;

CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    debt_id INTEGER REFERENCES debts(id),
    debtor_id UUID REFERENCES debtors(id),
    email_to VARCHAR(255) NOT NULL,
    email_from VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    template_id VARCHAR(255),
    sendgrid_message_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    bounced_at TIMESTAMP WITH TIME ZONE,
    bounce_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    template_id VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_email_logs_sendgrid_message_id
    ON email_logs(sendgrid_message_id);

CREATE INDEX IF NOT EXISTS idx_email_logs_debt_id
    ON email_logs(debt_id);

CREATE INDEX IF NOT EXISTS idx_email_logs_debtor_id
    ON email_logs(debtor_id);
