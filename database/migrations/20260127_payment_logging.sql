-- Add audit fields for payments, scheduled payments, and account records
ALTER TABLE debts
    ADD COLUMN IF NOT EXISTS total_paid_amount DECIMAL(12, 2) DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS last_payment_id INTEGER,
    ADD COLUMN IF NOT EXISTS last_payment_reference VARCHAR(255),
    ADD COLUMN IF NOT EXISTS last_payment_method VARCHAR(50);

ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS transaction_reference VARCHAR(255),
    ADD COLUMN IF NOT EXISTS scheduled_payment_id INTEGER,
    ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);

ALTER TABLE scheduled_payments
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS transaction_reference VARCHAR(255),
    ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);
