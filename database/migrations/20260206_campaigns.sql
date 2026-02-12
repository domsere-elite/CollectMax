-- Add email campaign tables
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    html_content TEXT,
    template_id VARCHAR(255),
    filters JSONB,
    status VARCHAR(50) DEFAULT 'draft',
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaign_recipients (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    debt_id INTEGER REFERENCES debts(id),
    debtor_id UUID REFERENCES debtors(id),
    email_to VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    sendgrid_message_id VARCHAR(255),
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_campaign_recipients_campaign_id
    ON campaign_recipients(campaign_id);

CREATE INDEX IF NOT EXISTS idx_campaign_recipients_debt_id
    ON campaign_recipients(debt_id);
