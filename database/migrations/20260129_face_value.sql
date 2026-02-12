ALTER TABLE debts
    ADD COLUMN IF NOT EXISTS face_value DECIMAL(12, 2);

UPDATE debts
SET face_value = amount_due + COALESCE(total_paid_amount, 0)
WHERE face_value IS NULL;
