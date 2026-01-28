from decimal import Decimal
from datetime import datetime
from app.services.usa_epay import USAePayService
from app.core.finance import calculate_split
from psycopg2.extras import RealDictCursor

class TransactionManager:
    def __init__(self, db_cursor):
        self.cursor = db_cursor
        self.usa_epay = USAePayService()

    def execute_payment(self, debt_id: int, amount: Decimal, card_token: str = None, is_scheduled: bool = False, plan_id: int = None, scheduled_payment_id: int = None):
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
                # Use debt_id as invoice for simple tracking
                epay_resp = self.usa_epay.run_transaction(
                    token_id=card_token,
                    amount=amount,
                    invoice=f"Debt-{debt_id}",
                    customer_data=customer_data
                )
                payment_ref = epay_resp.get("refnum", "USAePay Tokenized")
            except Exception as e:
                # MARK AS DECLINED IF SCHEDULED
                if scheduled_payment_id:
                    self.cursor.execute("""
                        UPDATE scheduled_payments 
                        SET status = 'declined',
                            processed_at = CURRENT_TIMESTAMP,
                            transaction_reference = NULL,
                            payment_method = %s
                        WHERE id = %s
                    """, (payment_method, scheduled_payment_id))
                raise Exception(f"USA ePay Transaction Failed: {str(e)}")

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
                transaction_reference, scheduled_payment_id, payment_method
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, timestamp
        """, (
            debt_id, amount, split['agency_portion'], split['client_portion'],
            payment_ref, scheduled_payment_id, payment_method
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
        if scheduled_payment_id:
            self.cursor.execute("""
                UPDATE scheduled_payments 
                SET status = 'paid',
                    actual_payment_id = %s,
                    processed_at = CURRENT_TIMESTAMP,
                    transaction_reference = %s,
                    payment_method = %s
                WHERE id = %s
            """, (new_payment['id'], payment_ref, payment_method, scheduled_payment_id))

        return {
            "payment_id": new_payment['id'],
            "ref_num": payment_ref,
            "amount": amount,
            "timestamp": new_payment['timestamp']
        }
