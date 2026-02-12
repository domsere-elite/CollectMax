UPDATE scheduled_payments sp
SET next_attempt_at = (
    (sp.due_date::timestamp AT TIME ZONE 'America/Chicago')
    + INTERVAL '5 hours'
    ) AT TIME ZONE 'UTC'
WHERE sp.status = 'pending'
  AND sp.next_attempt_at IS NULL
  AND sp.due_date > (NOW() AT TIME ZONE 'America/Chicago')::date
  AND sp.created_at < (sp.due_date::timestamp AT TIME ZONE 'America/Chicago');
