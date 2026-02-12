from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.services.usa_epay import USAePayService, USAePayDecline, USAePayError
from app.services.decline import classify_decline

class TransactionManager:
    def __init__(self, db_cursor):
        self.cursor = db_cursor
        self.usa_epay = USAePayService()

    def execute_payment(
        self,
        debt_id: int,
        amount: Decimal,
        card_token: Optional[str] = None,
        is_scheduled: bool = False,
        plan_id: Optional[int] = None,
        scheduled_payment_id: Optional[int] = None,
        attempt_count: Optional[int] = None,
        update_scheduled: bool = True,
        raise_on_decline: bool = True,
    ):
        """
        1. Executes charge via USA ePay (if card_token provided)
        2. Calculates split
        3. Records payment in 'payments' table
        4. Updates 'debts' table (balance, total_paid, last_payment)
        5. Marks 'scheduled_payments' as paid (if applicable)
        """
        # 1. Run Transaction if token exists
        payment_ref = "Internal - No Token"
        payment_method = "internal"
        result_code = None
        result_text = None
        gateway_key = None
        error_text = None
        if card_token:
            payment_method = "card_token"
            # Fetch debtor information for USA ePay reporting/AVS
            self.cursor.execute("""
                SELECT 
                    dr.first_name, dr.last_name, dr.email, dr.address_1, dr.address_2, dr.city, dr.state, dr.zip_code, dr.phone,
                    d.client_reference_number
                FROM debts d
                JOIN debtors dr ON d.debtor_id = dr.id
                WHERE d.id = %s
            """, (debt_id,))
            debtor = self.cursor.fetchone()
            
            customer_data = {}
            if debtor:
                customer_data = {
                    "first_name": debtor['first_name'],
                    "last_name": debtor['last_name'],
                    "email": debtor['email'],
                    "custid": debtor['client_reference_number'],
                    "address": debtor['address_1'],
                    "address2": debtor['address_2'],
                    "city": debtor['city'],
                    "state": debtor['state'],
                    "zip": debtor['zip_code'],
                    "phone": debtor['phone']
                }

            try:
                stored_credential = "installment" if scheduled_payment_id else None
                # Use debt_id as invoice for simple tracking
                attempt_suffix = attempt_count if attempt_count is not None else 1
                invoice_id = f"Debt-{debt_id}-SP{scheduled_payment_id or 'manual'}-A{attempt_suffix}"
                epay_resp = self.usa_epay.run_transaction(
                    token_id=card_token,
                    amount=amount,
                    invoice=invoice_id,
                    customer_data=customer_data,
                    stored_credential=stored_credential
                )
                payment_ref = epay_resp.get("refnum", "USAePay Tokenized")
                gateway_key = epay_resp.get("key")
                result_code = epay_resp.get("result_code", "A")
                result_text = epay_resp.get("result", "Approved")
            except USAePayDecline as e:
                decline_data = e.data or {}
                payment_ref = decline_data.get("refnum")
                gateway_key = decline_data.get("key")
                result_code = decline_data.get("result_code", "D")
                result_text = decline_data.get("result") or str(e)
                error_text = str(e)
                decline_reason = classify_decline(result_text)

                self.cursor.execute(
                    """
                    INSERT INTO payments (
                        debt_id, amount_paid, agency_portion, client_portion,
                        transaction_reference, scheduled_payment_id, payment_method,
                        status, result_code, result, decline_reason, error_message
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'declined', %s, %s, %s, %s)
                    RETURNING id, timestamp
                    """,
                    (
                        debt_id,
                        amount,
                        Decimal("0.00"),
                        Decimal("0.00"),
                        payment_ref,
                        scheduled_payment_id,
                        payment_method,
                        result_code,
                        result_text,
                        decline_reason,
                        error_text,
                    ),
                )
                new_payment = self.cursor.fetchone()

                if update_scheduled and scheduled_payment_id:
                    self.cursor.execute(
                        """
                        UPDATE scheduled_payments
                        SET status = 'declined',
                            actual_payment_id = %s,
                            processed_at = CURRENT_TIMESTAMP,
                            transaction_reference = %s,
                            payment_method = %s,
                            last_gateway_trankey = %s,
                            last_result_code = %s,
                            last_result = %s,
                            last_decline_reason = %s,
                            last_error = %s,
                            attempt_count = COALESCE(attempt_count, 0) + 1,
                            next_attempt_at = NULL
                        WHERE id = %s
                        """,
                        (
                            new_payment["id"],
                            payment_ref,
                            payment_method,
                            gateway_key,
                            result_code,
                            result_text,
                            decline_reason,
                            error_text,
                            scheduled_payment_id,
                        ),
                    )

                if raise_on_decline:
                    raise Exception(f"USA ePay Transaction Declined: {result_text}")

                return {
                    "status": "declined",
                    "payment_id": new_payment["id"],
                    "ref_num": payment_ref,
                    "amount": amount,
                    "timestamp": new_payment["timestamp"],
                    "result_code": result_code,
                    "result": result_text,
                    "decline_reason": decline_reason,
                    "payment_method": payment_method,
                    "gateway_key": gateway_key,
                    "error": error_text,
                }
            except USAePayError as e:
                error_text = str(e)
                decline_reason = classify_decline(error_text)
                self.cursor.execute(
                    """
                    INSERT INTO payments (
                        debt_id, amount_paid, agency_portion, client_portion,
                        transaction_reference, scheduled_payment_id, payment_method,
                        status, result_code, result, decline_reason, error_message
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'declined', %s, %s, %s, %s)
                    RETURNING id, timestamp
                    """,
                    (
                        debt_id,
                        amount,
                        Decimal("0.00"),
                        Decimal("0.00"),
                        None,
                        scheduled_payment_id,
                        payment_method,
                        "E",
                        "Error",
                        decline_reason,
                        error_text,
                    ),
                )
                new_payment = self.cursor.fetchone()

                if update_scheduled and scheduled_payment_id:
                    self.cursor.execute(
                        """
                        UPDATE scheduled_payments
                        SET status = 'declined',
                            actual_payment_id = %s,
                            processed_at = CURRENT_TIMESTAMP,
                            transaction_reference = NULL,
                            payment_method = %s,
                            last_gateway_trankey = NULL,
                            last_result_code = %s,
                            last_result = %s,
                            last_decline_reason = %s,
                            last_error = %s,
                            attempt_count = COALESCE(attempt_count, 0) + 1,
                            next_attempt_at = NULL
                        WHERE id = %s
                        """,
                        (
                            new_payment["id"],
                            payment_method,
                            "E",
                            "Error",
                            decline_reason,
                            error_text,
                            scheduled_payment_id,
                        ),
                    )

                if raise_on_decline:
                    raise Exception(f"USA ePay Transaction Failed: {error_text}")

                return {
                    "status": "declined",
                    "payment_id": new_payment["id"],
                    "ref_num": None,
                    "amount": amount,
                    "timestamp": new_payment["timestamp"],
                    "result_code": "E",
                    "result": "Error",
                    "decline_reason": decline_reason,
                    "payment_method": payment_method,
                    "gateway_key": None,
                    "error": error_text,
                }

        # 2. Get Portfolio Commission for Split
        self.cursor.execute("""
            SELECT p.commission_percentage 
            FROM debts d 
            JOIN portfolios p ON d.portfolio_id = p.id 
            WHERE d.id = %s
        """, (debt_id,))
        res = self.cursor.fetchone()
        commission_rate = res['commission_percentage'] if res else Decimal("30.0")
        
        split = calculate_split(amount, commission_rate)

        # 3. Record Payment
        self.cursor.execute("""
            INSERT INTO payments (
                debt_id, amount_paid, agency_portion, client_portion,
                transaction_reference, scheduled_payment_id, payment_method,
                status, result_code, result, error_message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'paid', %s, %s, NULL)
            RETURNING id, timestamp
        """, (
            debt_id, amount, split['agency_portion'], split['client_portion'],
            payment_ref, scheduled_payment_id, payment_method,
            result_code or "A", result_text or "Approved"
        ))
        new_payment = self.cursor.fetchone()

        # 4. Update Debt Record
        self.cursor.execute("""
            UPDATE debts 
            SET amount_due = amount_due - %s,
                total_paid_amount = total_paid_amount + %s,
                last_payment_date = CURRENT_DATE,
                last_payment_amount = %s,
                last_payment_id = %s,
                last_payment_reference = %s,
                last_payment_method = %s,
                status = CASE 
                    WHEN (amount_due - %s) <= 0 THEN 'Paid'::debt_status 
                    ELSE status 
                END
            WHERE id = %s
        """, (amount, amount, amount, new_payment['id'], payment_ref, payment_method, amount, debt_id))

        # 5. Update Scheduled Payment status
        if scheduled_payment_id and update_scheduled:
            self.cursor.execute("""
                UPDATE scheduled_payments 
                SET status = 'paid',
                    actual_payment_id = %s,
                    processed_at = CURRENT_TIMESTAMP,
                    transaction_reference = %s,
                    payment_method = %s,
                    last_gateway_trankey = %s,
                    last_result_code = %s,
                    last_result = %s,
                    last_decline_reason = NULL,
                    last_error = NULL,
                    next_attempt_at = NULL
                WHERE id = %s
            """, (new_payment['id'], payment_ref, payment_method, gateway_key, result_code or "A", result_text or "Approved", scheduled_payment_id))

        return {
            "status": "paid",
            "payment_id": new_payment['id'],
            "ref_num": payment_ref,
            "amount": amount,
            "timestamp": new_payment['timestamp'],
            "result_code": result_code or "A",
            "result": result_text or "Approved",
            "payment_method": payment_method,
            "gateway_key": gateway_key,
        }
