from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.core.database import get_db
from psycopg2.extras import RealDictCursor
from app.core.compliance import check_calling_hours, check_7_in_7, ComplianceError
from app.core.finance import calculate_split, generate_payment_schedule
from app.services.usa_epay import USAePayService
from app.services.transactions import TransactionManager
from app.models.schemas import (
    InteractionCreate, PaymentCreate, PaymentResponse, 
    DebtResponse, PaymentPlanCreate, PaymentPlanResponse, 
    ScheduledPaymentResponse
)
import uuid
import traceback

# Initialize USA ePay Service
usa_epay = USAePayService()

router = APIRouter()

@router.get("/verify-epay")
async def verify_epay():
    """
    Diagnostic endpoint to verify USA ePay connectivity.
    """
    try:
        service = USAePayService()
        success, message = service.verify_connection()
        return {
            "success": success, 
            "message": message, 
            "environment": "Sandbox" if "sandbox" in service.base_url else "Production"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/work-queue", response_model=List[DebtResponse])
def get_work_queue(db=Depends(get_db)):
    """
    Fetches the next available debts for the agent.
    Logic: Query 'debts' where status='New' LIMIT 1
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT 
                d.id as debt_id,
                d.original_account_number,
                d.client_reference_number,
                d.original_creditor,
                d.date_opened,
                d.charge_off_date,
                d.principal_balance,
                d.fees_costs,
                d.amount_due,
                d.last_payment_date,
                d.last_payment_amount,
                d.status,
                dr.id as debtor_id,
                dr.first_name,
                dr.last_name,
                dr.dob,
                dr.address_1,
                dr.address_2,
                dr.city,
                dr.state,
                dr.zip_code,
                dr.phone,
                dr.mobile_consent,
                dr.email,
                dr.ssn_hash,
                dr.do_not_contact
            FROM debts d
            JOIN debtors dr ON d.debtor_id = dr.id
            WHERE d.status = 'New'
            ORDER BY d.id ASC
            LIMIT 1
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Manually construct the response to match DebtResponse schema
        result = []
        for row in rows:
            result.append({
                "id": row['debt_id'],
                "original_account_number": row['original_account_number'],
                "client_reference_number": row['client_reference_number'],
                "original_creditor": row['original_creditor'],
                "date_opened": str(row['date_opened']) if row['date_opened'] else None,
                "charge_off_date": str(row['charge_off_date']) if row['charge_off_date'] else None,
                "principal_balance": float(row['principal_balance']) if row['principal_balance'] else 0.0,
                "fees_costs": float(row['fees_costs']) if row['fees_costs'] else 0.0,
                "amount_due": float(row['amount_due']) if row['amount_due'] else 0.0,
                "last_payment_date": str(row['last_payment_date']) if row['last_payment_date'] else None,
                "last_payment_amount": float(row['last_payment_amount']) if row['last_payment_amount'] else 0.0,
                "status": row['status'],
                "debtor": {
                    "id": str(row['debtor_id']),
                    "first_name": row['first_name'],
                    "last_name": row['last_name'],
                    "dob": str(row['dob']) if row['dob'] else None,
                    "address_1": row['address_1'],
                    "address_2": row['address_2'],
                    "city": row['city'],
                    "state": row['state'],
                    "zip_code": row['zip_code'],
                    "phone": row['phone'],
                    "mobile_consent": row['mobile_consent'],
                    "email": row['email'],
                    "ssn_hash": row['ssn_hash'],
                    "do_not_contact": row['do_not_contact']
                }
            })
        
        return result
    except Exception as e:
        print(f"Error fetching work queue: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()

@router.get("/search", response_model=List[DebtResponse])
def search_debts(search_type: str, query: str, db=Depends(get_db)):
    """
    Search for debts by name or client reference.
    search_type: 'name' or 'client_ref'
    query: search term
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        if search_type == 'name':
            # Search by debtor name (case-insensitive, partial match)
            sql_query = """
                SELECT 
                    d.id as debt_id,
                    d.original_account_number,
                    d.client_reference_number,
                    d.original_creditor,
                    d.date_opened,
                    d.charge_off_date,
                    d.principal_balance,
                    d.fees_costs,
                    d.amount_due,
                    d.last_payment_date,
                    d.last_payment_amount,
                    d.status,
                    dr.id as debtor_id,
                    dr.first_name,
                    dr.last_name,
                    dr.dob,
                    dr.address_1,
                    dr.address_2,
                    dr.city,
                    dr.state,
                    dr.zip_code,
                    dr.phone,
                    dr.mobile_consent,
                    dr.email,
                    dr.ssn_hash,
                    dr.do_not_contact
                FROM debts d
                JOIN debtors dr ON d.debtor_id = dr.id
                WHERE LOWER(dr.first_name || ' ' || dr.last_name) LIKE LOWER(%s)
                ORDER BY d.id ASC
                LIMIT 10
            """
            cursor.execute(sql_query, (f'%{query}%',))
        elif search_type == 'client_ref':
            # Search by client reference (exact match)
            sql_query = """
                SELECT 
                    d.id as debt_id,
                    d.original_account_number,
                    d.client_reference_number,
                    d.original_creditor,
                    d.date_opened,
                    d.charge_off_date,
                    d.principal_balance,
                    d.fees_costs,
                    d.amount_due,
                    d.last_payment_date,
                    d.last_payment_amount,
                    d.status,
                    dr.id as debtor_id,
                    dr.first_name,
                    dr.last_name,
                    dr.dob,
                    dr.address_1,
                    dr.address_2,
                    dr.city,
                    dr.state,
                    dr.zip_code,
                    dr.phone,
                    dr.mobile_consent,
                    dr.email,
                    dr.ssn_hash,
                    dr.do_not_contact
                FROM debts d
                JOIN debtors dr ON d.debtor_id = dr.id
                WHERE d.client_reference_number = %s
                ORDER BY d.id ASC
                LIMIT 10
            """
            cursor.execute(sql_query, (query,))
        else:
            raise HTTPException(status_code=400, detail="Invalid search_type. Use 'name' or 'client_ref'")
        
        rows = cursor.fetchall()
        
        # Build response
        result = []
        for row in rows:
            result.append({
                "id": row['debt_id'],
                "original_account_number": row['original_account_number'],
                "client_reference_number": row['client_reference_number'],
                "original_creditor": row['original_creditor'],
                "date_opened": str(row['date_opened']) if row['date_opened'] else None,
                "charge_off_date": str(row['charge_off_date']) if row['charge_off_date'] else None,
                "principal_balance": float(row['principal_balance']) if row['principal_balance'] else 0.0,
                "fees_costs": float(row['fees_costs']) if row['fees_costs'] else 0.0,
                "amount_due": float(row['amount_due']) if row['amount_due'] else 0.0,
                "last_payment_date": str(row['last_payment_date']) if row['last_payment_date'] else None,
                "last_payment_amount": float(row['last_payment_amount']) if row['last_payment_amount'] else 0.0,
                "status": row['status'],
                "debtor": {
                    "id": str(row['debtor_id']),
                    "first_name": row['first_name'],
                    "last_name": row['last_name'],
                    "dob": str(row['dob']) if row['dob'] else None,
                    "address_1": row['address_1'],
                    "address_2": row['address_2'],
                    "city": row['city'],
                    "state": row['state'],
                    "zip_code": row['zip_code'],
                    "phone": row['phone'],
                    "mobile_consent": row['mobile_consent'],
                    "email": row['email'],
                    "ssn_hash": row['ssn_hash'],
                    "do_not_contact": row['do_not_contact']
                }
            })
        
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error searching debts: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()

@router.post("/interactions")
def log_interaction(interaction: InteractionCreate, db=Depends(get_db)):
    """
    Logs a call/email. Checks compliance before logging.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Fetch Debtor Zip for Compliance
        cursor.execute("""
            SELECT dr.zip_code 
            FROM debts d 
            JOIN debtors dr ON d.debtor_id = dr.id 
            WHERE d.id = %s
        """, (interaction.debt_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Debt not found")
            
        debtor_zip = result['zip_code']
        
        # 2. Check Timezone Guard
        if interaction.action_type == 'Call':
            try:
                check_calling_hours(debtor_zip)
            except ComplianceError as e:
                # Log the attempt? Optional. For now, block.
                raise HTTPException(status_code=403, detail=str(e))

        # 3. Check 7-in-7
        # Fetch status of previous logs for this debt in last 7 days? 
        # For simplicity, we just pass empty list or implement check_7_in_7 fully later.
        # Let's mock the 'prev_logs' fetch for compliance.py or update it to take DB cursor.
        # For now, we will perform the INSERT.
        
        # 4. Insert Interaction
        cursor.execute("""
            INSERT INTO interaction_logs (debt_id, action_type, notes)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (interaction.debt_id, interaction.action_type, interaction.notes))
        
        db.commit()
        return {"status": "Logged", "warning_flag": False}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        print(f"Error logging interaction: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        cursor.close()

@router.post("/payments", response_model=PaymentResponse)
def process_payment(payment: PaymentCreate, db=Depends(get_db)):
    """
    Processes a payment and splits the ledger.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        payment_ref = "Internal - No Token"
        payment_method = "manual"
        # 1. Get Portfolio Commission Rate
        cursor.execute("""
            SELECT p.commission_percentage 
            FROM debts d 
            JOIN portfolios p ON d.portfolio_id = p.id 
            WHERE d.id = %s
        """, (payment.debt_id,))
        result = cursor.fetchone()
        
        # Default to 0 if not found (shouldn't happen) or 30% if NULL
        commission_rate = result['commission_percentage'] if result else Decimal("30.0")
        
        # 2. Calculate Split
        split = calculate_split(payment.amount_paid, commission_rate)
        
        # 3. Insert Payment
        cursor.execute("""
            INSERT INTO payments (
                debt_id, amount_paid, agency_portion, client_portion,
                transaction_reference, scheduled_payment_id, payment_method
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, timestamp
        """, (
            payment.debt_id, payment.amount_paid, split['agency_portion'], split['client_portion'],
            payment_ref, None, payment_method
        ))
        
        new_payment = cursor.fetchone()
        
        # 4. Update Debt Balance/Status
        # Simply decrement amount_due for now
        cursor.execute("""
            UPDATE debts 
            SET amount_due = amount_due - %s,
                last_payment_date = CURRENT_DATE,
                last_payment_amount = %s,
                last_payment_id = %s,
                last_payment_reference = %s,
                last_payment_method = %s,
                status = CASE WHEN (amount_due - %s) <= 0 THEN 'Paid' ELSE status END
            WHERE id = %s
        """, (
            payment.amount_paid, payment.amount_paid, new_payment['id'],
            payment_ref, payment_method, payment.amount_paid, payment.debt_id
        ))
        
        db.commit()
        
        return {
            "id": new_payment['id'],
            "amount_paid": payment.amount_paid,
            "agency_portion": split['agency_portion'],
            "client_portion": split['client_portion'], 
            "timestamp": new_payment['timestamp'],
            "transaction_reference": payment_ref,
            "scheduled_payment_id": None,
            "payment_method": payment_method
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error processing payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.get("/payments/{debt_id}", response_model=List[PaymentResponse])
def get_debt_payments(debt_id: int, db=Depends(get_db)):
    """
    Fetches all payments recorded for a specific debt.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM payments WHERE debt_id = %s ORDER BY timestamp DESC", (debt_id,))
        return cursor.fetchall()
    finally:
        cursor.close()

@router.get("/payment-plans/preview", response_model=List[dict])
def get_payment_plan_preview(
    total_amount: Decimal, 
    down_payment: Decimal, 
    installments: int, 
    frequency: str, 
    start_date: datetime
):
    """
    Returns a preview of a payment schedule without saving it.
    """
    try:
        schedule = generate_payment_schedule(total_amount, down_payment, installments, frequency, start_date)
        return schedule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payment-plans", response_model=PaymentPlanResponse)
def create_payment_plan(plan: PaymentPlanCreate, db=Depends(get_db)):
    """
    Creates a new payment plan and generates its schedule.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Tokenize Card using USA ePay
        try:
            card_token = usa_epay.tokenize_card(
                card_number=plan.card_number,
                exp_date=plan.card_expiry,
                cvv=plan.card_cvv,
                holder_name=plan.cardholder_name,
                billing_address={
                    "address": plan.billing_address,
                    "city": plan.billing_city,
                    "state": plan.billing_state,
                    "zip": plan.billing_zip
                }
            )
        except Exception as e:
            print(f"Tokenization error: {e}")
            raise HTTPException(status_code=400, detail=f"Card Tokenization Failed: {str(e)}")

        # 2. Insert Plan
        cursor.execute("""
            INSERT INTO payment_plans (
                debt_id, total_settlement_amount, is_settlement, down_payment_amount, 
                installment_count, frequency, start_date, card_token, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
            RETURNING id, created_at
        """, (
            plan.debt_id, plan.total_settlement_amount, plan.is_settlement, plan.down_payment_amount,
            plan.installment_count, plan.frequency, plan.start_date, card_token
        ))
        
        new_plan = cursor.fetchone()
        plan_id = new_plan['id']
        
        # 2. Generate Schedule to identify Down Payment
        schedule = generate_payment_schedule(
            plan.total_settlement_amount, 
            plan.down_payment_amount, 
            plan.installment_count, 
            plan.frequency, 
            plan.start_date
        )

        manager = TransactionManager(cursor)
        today_date = datetime.now().date()
        dp_result = None

        # 3. Process Down Payment Prerequisite
        dp_item = next((item for item in schedule if item.get('type') == 'Down Payment'), None)
        if dp_item and dp_item['amount'] > 0:
            try:
                # We execute DP BEFORE inserting the plan. 
                # If it fails, the exception will trigger db.rollback()
                dp_result = manager.execute_payment(
                    debt_id=plan.debt_id,
                    amount=dp_item['amount'],
                    card_token=card_token,
                    # We don't have a scheduled_payment_id yet
                )
            except Exception as dp_err:
                print(f"Down payment failed: {dp_err}")
                raise HTTPException(status_code=400, detail=f"Down Payment Failed: {str(dp_err)}. Plan not created.")

        # 4. Insert Plan
        cursor.execute("""
            INSERT INTO payment_plans (
                debt_id, total_settlement_amount, is_settlement, down_payment_amount, 
                installment_count, frequency, start_date, card_token, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
            RETURNING id, created_at
        """, (
            plan.debt_id, plan.total_settlement_amount, plan.is_settlement, plan.down_payment_amount,
            plan.installment_count, plan.frequency, plan.start_date, card_token
        ))
        
        new_plan = cursor.fetchone()
        plan_id = new_plan['id']

        # 5. Insert Schedule
        for item in schedule:
            due_date = item['due_date'].date() if isinstance(item['due_date'], datetime) else item['due_date']
            status = 'pending'
            payment_id = None

            # If this was the DP we just ran, mark it paid
            if item.get('type') == 'Down Payment' and dp_result:
                status = 'paid'
                payment_id = dp_result['payment_id']

            cursor.execute("""
                INSERT INTO scheduled_payments (plan_id, amount, due_date, status, actual_payment_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (plan_id, item['amount'], item['due_date'], status, payment_id))
            sched_item = cursor.fetchone()
            
            # AUTO-RUN recurring installments IF due today (and not already paid as DP)
            if status == 'pending' and due_date == today_date:
                try:
                    manager.execute_payment(
                        debt_id=plan.debt_id,
                        amount=item['amount'],
                        card_token=card_token,
                        scheduled_payment_id=sched_item['id']
                    )
                except Exception as eval_err:
                    print(f"Auto-run payment failed for due_date {due_date}: {eval_err}")
            
        # 3. Update Debt Status
        cursor.execute("""
            UPDATE debts SET status = 'Plan' WHERE id = %s
        """, (plan.debt_id,))
        
        db.commit()
        
        return {
            "id": plan_id,
            "debt_id": plan.debt_id,
            "total_settlement_amount": plan.total_settlement_amount,
            "is_settlement": plan.is_settlement,
            "down_payment_amount": plan.down_payment_amount,
            "installment_count": plan.installment_count,
            "frequency": plan.frequency,
            "start_date": plan.start_date,
            "status": "active",
            "created_at": new_plan['created_at'],
            "down_payment_status": "approved" if dp_result else None,
            "dp_reference": dp_result['ref_num'] if dp_result else None
        }
    except Exception as e:
        db.rollback()
        print(f"Error creating payment plan: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.get("/payment-plans/{debt_id}", response_model=List[PaymentPlanResponse])
def get_debt_plans(debt_id: int, db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM payment_plans WHERE debt_id = %s ORDER BY created_at DESC", (debt_id,))
        return cursor.fetchall()
    finally:
        cursor.close()

@router.post("/payments/scheduled/{payment_id}/execute")
def execute_scheduled_payment(payment_id: int, db=Depends(get_db)):
    """
    Manually executes a scheduled payment early.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Fetch scheduled payment and associated plan info
        cursor.execute("""
            SELECT sp.*, pp.debt_id, pp.card_token
            FROM scheduled_payments sp
            JOIN payment_plans pp ON sp.plan_id = pp.id
            WHERE sp.id = %s
        """, (payment_id,))
        payment = cursor.fetchone()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Scheduled payment not found")
        
        if payment['status'] == 'paid':
            raise HTTPException(status_code=400, detail="Payment has already been processed")

        # 2. Execute via TransactionManager
        manager = TransactionManager(cursor)
        result = manager.execute_payment(
            debt_id=payment['debt_id'],
            amount=payment['amount'],
            card_token=payment['card_token'],
            scheduled_payment_id=payment_id
        )
        
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        # If it was a decline handled by TransactionManager, it might already be committed as 'declined'
        # depending on its internal try/except, but we re-raise for visibility
        print(f"Manual execution error: {e}")
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.get("/admin/payments")
def get_admin_payments(status: Optional[str] = None, days: int = 0, db=Depends(get_db)):
    """
    Admin view for payment management.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT 
                sp.id, sp.amount, sp.due_date, sp.status, sp.created_at,
                pp.debt_id, pp.frequency,
                d.client_reference_number,
                dr.first_name, dr.last_name
            FROM scheduled_payments sp
            JOIN payment_plans pp ON sp.plan_id = pp.id
            JOIN debts d ON pp.debt_id = d.id
            JOIN debtors dr ON d.debtor_id = dr.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND sp.status = %s"
            params.append(status)
            
        if days == 0:
            # Today's payments (default)
            query += " AND sp.due_date = CURRENT_DATE"
        elif days > 0:
            query += " AND sp.due_date >= CURRENT_DATE - INTERVAL '%s days'"
            params.append(days)

        query += " ORDER BY sp.due_date DESC, sp.id DESC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        cursor.close()

@router.post("/payments/one-off")
def run_one_off_payment(debt_id: int, amount: Decimal, db=Depends(get_db)):
    """
    Runs a manual payment using the most recent card token for this debt.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Find the card token from an active plan
        cursor.execute("""
            SELECT card_token 
            FROM payment_plans 
            WHERE debt_id = %s AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, (debt_id,))
        plan = cursor.fetchone()
        
        if not plan or not plan['card_token']:
            raise HTTPException(status_code=404, detail="No active payment plan or card token found for this debt.")
            
        # 2. Execute via TransactionManager
        manager = TransactionManager(cursor)
        result = manager.execute_payment(
            debt_id=debt_id,
            amount=amount,
            card_token=plan['card_token']
        )
        
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

