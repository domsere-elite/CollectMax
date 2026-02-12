from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from psycopg2.extras import RealDictCursor

from app.core.database import get_db_connection
from app.services.decline import classify_decline
from app.services.transactions import TransactionManager


CT_TZ = ZoneInfo("America/Chicago")


def _due_at_ct(due_date, hour: int) -> datetime:
    return datetime.combine(due_date, time(hour, 0), tzinfo=CT_TZ)


def _next_attempt_timestamp(due_date, attempt_count: int) -> datetime | None:
    if attempt_count == 1:
        return _due_at_ct(due_date, 17)
    if attempt_count == 2:
        return _due_at_ct(due_date + timedelta(days=1), 5)
    return None


def run_due_scheduled_payments(run_window: str, batch_limit: int = 200) -> dict:
    now_utc = datetime.now(timezone.utc)
    now_ct = now_utc.astimezone(CT_TZ)

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    processed = 0
    declined = 0
    retried = 0

    try:
        cursor.execute(
            """
            SELECT 
                sp.id, sp.plan_id, sp.amount, sp.due_date, sp.status,
                sp.attempt_count, sp.next_attempt_at, sp.created_at,
                pp.debt_id, pp.card_token
            FROM scheduled_payments sp
            JOIN payment_plans pp ON sp.plan_id = pp.id
            WHERE pp.status = 'active'
              AND sp.status IN ('pending', 'retrying')
              AND sp.next_attempt_at IS NOT NULL
              AND sp.next_attempt_at <= %s
              AND sp.created_at < (sp.due_date::timestamp AT TIME ZONE 'America/Chicago')
            ORDER BY sp.next_attempt_at ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED
            """,
            (now_utc, batch_limit)
        )
        rows = cursor.fetchall()

        for row in rows:
            attempt_count = (row.get("attempt_count") or 0) + 1

            cursor.execute(
                """
                UPDATE scheduled_payments
                SET status = 'processing',
                    last_attempt_at = %s,
                    attempt_count = %s
                WHERE id = %s
                """,
                (now_utc, attempt_count, row["id"])
            )

            manager = TransactionManager(cursor)
            result = manager.execute_payment(
                debt_id=row["debt_id"],
                amount=row["amount"],
                card_token=row["card_token"],
                scheduled_payment_id=row["id"],
                attempt_count=attempt_count,
                update_scheduled=False,
                raise_on_decline=False
            )

            if result.get("status") == "paid":
                cursor.execute(
                    """
                    UPDATE scheduled_payments
                    SET status = 'paid',
                        actual_payment_id = %s,
                        processed_at = %s,
                        transaction_reference = %s,
                        payment_method = %s,
                        last_gateway_trankey = %s,
                        last_result_code = %s,
                        last_result = %s,
                        last_decline_reason = NULL,
                        last_error = NULL,
                        next_attempt_at = NULL
                    WHERE id = %s
                    """,
                    (
                        result.get("payment_id"),
                        now_utc,
                        result.get("ref_num"),
                        result.get("payment_method"),
                        result.get("gateway_key"),
                        result.get("result_code"),
                        result.get("result"),
                        row["id"],
                    )
                )
                processed += 1
                continue

            result_text = result.get("result") or result.get("error") or ""
            decline_reason = result.get("decline_reason") or classify_decline(result_text)
            retry_at_ct = None

            if decline_reason == "insufficient_funds":
                retry_at_ct = _next_attempt_timestamp(row["due_date"], attempt_count)

            if retry_at_ct:
                retry_at_utc = retry_at_ct.astimezone(timezone.utc)
                cursor.execute(
                    """
                    UPDATE scheduled_payments
                    SET status = 'retrying',
                        processed_at = %s,
                        transaction_reference = %s,
                        payment_method = %s,
                        last_gateway_trankey = %s,
                        last_result_code = %s,
                        last_result = %s,
                        last_decline_reason = %s,
                        last_error = %s,
                        next_attempt_at = %s
                    WHERE id = %s
                    """,
                    (
                        now_utc,
                        result.get("ref_num"),
                        result.get("payment_method"),
                        result.get("gateway_key"),
                        result.get("result_code"),
                        result.get("result"),
                        decline_reason,
                        result.get("error"),
                        retry_at_utc,
                        row["id"],
                    )
                )
                retried += 1
            else:
                cursor.execute(
                    """
                    UPDATE scheduled_payments
                    SET status = 'declined',
                        processed_at = %s,
                        transaction_reference = %s,
                        payment_method = %s,
                        last_gateway_trankey = %s,
                        last_result_code = %s,
                        last_result = %s,
                        last_decline_reason = %s,
                        last_error = %s,
                        next_attempt_at = NULL
                    WHERE id = %s
                    """,
                    (
                        now_utc,
                        result.get("ref_num"),
                        result.get("payment_method"),
                        result.get("gateway_key"),
                        result.get("result_code"),
                        result.get("result"),
                        decline_reason,
                        result.get("error"),
                        row["id"],
                    )
                )
                declined += 1

        conn.commit()
        return {
            "run_window": run_window,
            "now_ct": now_ct.isoformat(),
            "processed": processed,
            "retried": retried,
            "declined": declined,
            "total": len(rows)
        }
    finally:
        cursor.close()
        conn.close()
