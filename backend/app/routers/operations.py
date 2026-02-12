from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import logging
import os
import calendar
from datetime import datetime, time, timezone, date, timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal
from app.core.database import get_db
from app.core.auth import require_auth
from psycopg2.extras import RealDictCursor
from app.core.compliance import check_calling_hours, ComplianceError
from app.core.finance import calculate_split, generate_payment_schedule
from app.services.usa_epay import USAePayService
from app.services.comms import CommsManager
from app.services.transactions import TransactionManager
from app.models.schemas import (
    InteractionCreate, EmailTemplateSend, DebtorEmailUpdate, ValidationNoticeSend, PaymentCreate, PaymentResponse, 
    DebtResponse, PaymentPlanCreate, PaymentPlanResponse, 
    ScheduledPaymentResponse
)
import uuid
import traceback

# Initialize USA ePay Service
usa_epay = USAePayService()
CT_TZ = ZoneInfo("America/Chicago")


def compute_next_attempt_at(due_date):
    due_ct = datetime.combine(due_date, time(5, 0), tzinfo=CT_TZ)
    return due_ct.astimezone(timezone.utc)


def _ct_day_bounds(target_date: date):
    start_ct = datetime.combine(target_date, time(0, 0), tzinfo=CT_TZ)
    end_ct = start_ct + timedelta(days=1)
    return start_ct.astimezone(timezone.utc), end_ct.astimezone(timezone.utc)


def _month_end(date_ct: date):
    last_day = calendar.monthrange(date_ct.year, date_ct.month)[1]
    return date(date_ct.year, date_ct.month, last_day)

router = APIRouter()
logger = logging.getLogger(__name__)


def _log_interaction(cursor, debt_id: int, action_type: str, notes: Optional[str], agent_id: Optional[str] = None):
    cursor.execute(
        """
        INSERT INTO interaction_logs (debt_id, agent_id, action_type, notes)
        VALUES (%s, %s, %s, %s)
        """,
        (debt_id, agent_id, action_type, notes or ""),
    )

@router.get("/ping")
def ping(db=Depends(get_db)):
    """Diagnostic ping."""
    from app.core.database import get_db_connection
    import os
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        db_status = "Connected"
    except Exception as e:
        db_status = f"Failed: {str(e)}"
    
    db_url = os.getenv("DATABASE_URL")
    masked_url = db_url.split("@")[-1] if db_url and "@" in db_url else "Unknown"
    
    return {
        "status": "Online",
        "database": db_status,
        "db_host": masked_url,
        "env": os.getenv("DB_SSLMODE", "Not Set")
    }

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

@router.get("/portfolios")
def list_portfolios(db=Depends(get_db)):
    """List all portfolios for dropdown selection."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    from app.core.audit import write_audit_log
    try:
        cursor.execute("""
            SELECT p.id, p.name, c.name as client_name 
            FROM portfolios p
            LEFT JOIN clients c ON p.client_id = c.id
            ORDER BY p.name
        """)
        return cursor.fetchall()
    finally:
        cursor.close()

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
                COALESCE(NULLIF(d.current_creditor, ''), c.name) as current_creditor,
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
            LEFT JOIN portfolios p ON d.portfolio_id = p.id
            LEFT JOIN clients c ON p.client_id = c.id
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
                "current_creditor": row.get('current_creditor'),
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

@router.get("/debts/{debt_id}", response_model=DebtResponse)
def get_debt_details(debt_id: int, db=Depends(get_db)):
    """
    Fetch a single debt by ID.
    Used for restoring state or direct access.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT 
                d.id as debt_id,
                d.original_account_number,
                d.client_reference_number,
                d.original_creditor,
                COALESCE(NULLIF(d.current_creditor, ''), c.name) as current_creditor,
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
            LEFT JOIN portfolios p ON d.portfolio_id = p.id
            LEFT JOIN clients c ON p.client_id = c.id
            WHERE d.id = %s
        """
        cursor.execute(query, (debt_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Debt not found")
            
        return {
            "id": row['debt_id'],
            "original_account_number": row['original_account_number'],
            "client_reference_number": row['client_reference_number'],
            "original_creditor": row['original_creditor'],
            "current_creditor": row.get('current_creditor'),
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
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching debt details: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")
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
                    COALESCE(NULLIF(d.current_creditor, ''), c.name) as current_creditor,
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
                LEFT JOIN portfolios p ON d.portfolio_id = p.id
                LEFT JOIN clients c ON p.client_id = c.id
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
                    COALESCE(NULLIF(d.current_creditor, ''), c.name) as current_creditor,
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
                LEFT JOIN portfolios p ON d.portfolio_id = p.id
                LEFT JOIN clients c ON p.client_id = c.id
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
                "current_creditor": row.get('current_creditor'),
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
def log_interaction(interaction: InteractionCreate, db=Depends(get_db), user=Depends(require_auth)):
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
                raise HTTPException(status_code=403, detail=str(e))

        # 3. Insert Interaction
        _log_interaction(
            cursor,
            interaction.debt_id,
            interaction.action_type,
            interaction.notes,
            agent_id=user.get("sub"),
        )
        
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

@router.get("/debts/{debt_id}/interactions")
def get_debt_interactions(debt_id: int, db=Depends(get_db)):
    """
    Fetch all interaction logs for a specific debt.
    Orders by most recent first.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT 
                id,
                action_type,
                notes,
                agent_id,
                created_at
            FROM interaction_logs
            WHERE debt_id = %s
            ORDER BY created_at DESC
        """, (debt_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching interactions: {e}")
        return []
    finally:
        cursor.close()

@router.post("/email/send")
def send_template_email(payload: EmailTemplateSend, db=Depends(get_db), user=Depends(require_auth)):
    """
    Send a template-based email for a specific debt.
    """
    print(f"[DEBUG_EMAIL] send_template_email called for debt_id: {payload.debt_id}, template_id: {payload.template_id}")
    cursor = db.cursor(cursor_factory=RealDictCursor)
    from app.core.audit import write_audit_log
    try:
        cursor.execute(
            """
            SELECT d.id AS debt_id, d.original_account_number, d.client_reference_number,
                   d.original_creditor, COALESCE(NULLIF(d.current_creditor, ''), c.name) as current_creditor, d.amount_due, d.status, d.charge_off_date,
                   dr.id AS debtor_id, dr.first_name, dr.last_name, dr.email,
                   dr.address_1, dr.city, dr.state, dr.zip_code
            FROM debts d
            JOIN debtors dr ON d.debtor_id = dr.id
            LEFT JOIN portfolios p ON d.portfolio_id = p.id
            LEFT JOIN clients c ON p.client_id = c.id
            WHERE d.id = %s
            """,
            (payload.debt_id,)
        )
        record = cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Debt not found")
        if not record.get("email"):
            raise HTTPException(status_code=400, detail="Debtor email not available")

        cursor.execute(
            """
            SELECT name, template_id
            FROM email_templates
            WHERE template_id = %s
            """,
            (payload.template_id,)
        )
        template = cursor.fetchone()
        if not template:
            template = {
                "name": "Agent Email Template",
                "template_id": payload.template_id
            }

        full_name = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip()
        amount_due = float(record.get("amount_due") or 0)
        today_date = date.today()
        dynamic_data = {
            "debtor_first_name": record.get("first_name"),
            "debtor_last_name": record.get("last_name"),
            "debtor_full_name": full_name,
            "debtor_email": record.get("email"),
            "debt_id": record.get("debt_id"),
            "account_number": record.get("original_account_number"),
            "client_reference": record.get("client_reference_number"),
            "original_creditor": record.get("original_creditor"),
            "amount_due": amount_due,
            "debt_status": record.get("status"),
            "first_name": record.get("first_name"),
            "last_name": record.get("last_name"),
            "balance": f"{amount_due:,.2f}",
            "consumer_id": record.get("client_reference_number"),
            "original_account_number": record.get("original_account_number"),
            "issuer": record.get("original_creditor"),
            "current_creditor": record.get("current_creditor") or record.get("original_creditor"),
            "charge_off_date": record.get("charge_off_date").strftime("%B %d, %Y") if record.get("charge_off_date") else "",
            "today_date": today_date.strftime("%B %d, %Y"),
            "date_plus_30": (today_date + timedelta(days=30)).strftime("%B %d, %Y"),
            "address_line_1": record.get("address_1"),
            "city": record.get("city"),
            "state": record.get("state"),
            "zip_code": record.get("zip_code"),
            "email_address": record.get("email"),
            "unsubscribe_link": os.getenv("UNSUBSCRIBE_URL", "http://localhost:5173/unsubscribe"),
        }

        comms = CommsManager(cursor)
        subject = template.get("name") or "Account Update"
        print(f"[DEBUG_EMAIL] Passing to comms.send_email: To={record.get('email')}, Template={template.get('template_id')}")
        result = comms.send_email(
            to_email=record.get("email"),
            subject=subject,
            html_content="<p></p>",
            debt_id=payload.debt_id,
            template_id=template.get("template_id"),
            dynamic_data=dynamic_data
        )

        if not result.get("success"):
            raise HTTPException(status_code=502, detail=result.get("error") or "Email send failed")

        # --- Post-send logging (non-critical) ---
        # Wrap each in try-except so a logging failure doesn't
        # return 500 when the email was actually sent successfully.
        try:
            _log_interaction(
                cursor,
                payload.debt_id,
                "Email",
                f"Template: {template.get('name')} ({template.get('template_id')})",
                agent_id=user.get("sub"),
            )
        except Exception as log_err:
            logger.warning(f"Failed to log interaction for debt {payload.debt_id}: {log_err}")

        try:
            write_audit_log(
                cursor,
                actor_id=user.get("sub"),
                action="email.template.sent",
                entity_type="debt",
                entity_id=str(payload.debt_id),
                metadata={
                    "template_id": template.get("template_id"),
                    "recipient": record.get("email"),
                    "message_id": result.get("message_id"),
                },
            )
        except Exception as audit_err:
            logger.warning(f"Failed to write audit log for debt {payload.debt_id}: {audit_err}")

        db.commit()
        return {"status": "sent", "message_id": result.get("message_id")}
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.put("/debts/{debt_id}/email")
def update_debtor_email(debt_id: int, payload: DebtorEmailUpdate, db=Depends(get_db), user=Depends(require_auth)):
    """
    Update debtor email for a specific debt.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    from app.core.audit import write_audit_log
    try:
        cursor.execute(
            """
            SELECT dr.id AS debtor_id
            FROM debts d
            JOIN debtors dr ON d.debtor_id = dr.id
            WHERE d.id = %s
            """,
            (debt_id,)
        )
        record = cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Debt not found")

        cursor.execute(
            """
            SELECT email
            FROM debtors
            WHERE id = %s
            """,
            (record["debtor_id"],)
        )
        existing = cursor.fetchone()
        previous_email = existing.get("email") if existing else None

        cursor.execute(
            """
            UPDATE debtors
            SET email = %s
            WHERE id = %s
            """,
            (payload.email, record["debtor_id"])
        )
        _log_interaction(
            cursor,
            debt_id,
            "Other",
            f"Email updated from '{previous_email}' to '{payload.email}'",
            agent_id=user.get("sub"),
        )
        write_audit_log(
            cursor,
            actor_id=user.get("sub"),
            action="debtor.email.updated",
            entity_type="debtor",
            entity_id=str(record["debtor_id"]),
            before={"email": previous_email},
            after={"email": payload.email},
            metadata={"debt_id": debt_id},
        )
        db.commit()
        return {"status": "updated", "email": payload.email}
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        logger.exception("Failed to update debtor email", extra={"debt_id": debt_id})
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()

@router.post("/validation/send")
def send_validation_notice(payload: ValidationNoticeSend, db=Depends(get_db), user=Depends(require_auth)):
    """
    Send a validation notice email with a PDF URL.
    """
    print(f"[DEBUG_EMAIL] send_validation_notice called for debt_id: {payload.debt_id}")
    cursor = db.cursor(cursor_factory=RealDictCursor)
    from app.core.audit import write_audit_log
    try:
        pdf_url = payload.pdf_url.strip()
        if not pdf_url or not pdf_url.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid PDF URL")

        cursor.execute(
            """
            SELECT d.id AS debt_id, dr.email
            FROM debts d
            JOIN debtors dr ON d.debtor_id = dr.id
            WHERE d.id = %s
            """,
            (payload.debt_id,)
        )
        record = cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Debt not found")
        if not record.get("email"):
            raise HTTPException(status_code=400, detail="Debtor email not available")

        comms = CommsManager(cursor)
        result = comms.send_validation_notice(
            debtor_email=record.get("email"),
            pdf_url=pdf_url,
            debt_id=payload.debt_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=502, detail=result.get("error") or "Email send failed")

        _log_interaction(
            cursor,
            payload.debt_id,
            "Email",
            "Validation notice sent",
            agent_id=user.get("sub"),
        )

        write_audit_log(
            cursor,
            actor_id=user.get("sub"),
            action="email.validation.sent",
            entity_type="debt",
            entity_id=str(payload.debt_id),
            metadata={
                "recipient": record.get("email"),
                "pdf_url": pdf_url,
                "message_id": result.get("message_id"),
            },
        )

        db.commit()
        return {"status": "sent", "message_id": result.get("message_id")}
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.post("/payments", response_model=PaymentResponse)
def process_payment(payment: PaymentCreate, db=Depends(get_db), user=Depends(require_auth)):
    """
    Processes a payment and splits the ledger.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    from app.core.audit import write_audit_log
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
                transaction_reference, scheduled_payment_id, payment_method,
                status, result_code, result, error_message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'paid', %s, %s, NULL)
            RETURNING id, timestamp
        """, (
            payment.debt_id, payment.amount_paid, split['agency_portion'], split['client_portion'],
            payment_ref, None, payment_method, "A", "Approved"
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
        
        write_audit_log(
            cursor,
            actor_id=user.get("sub"),
            action="payment.processed",
            entity_type="payment",
            entity_id=str(new_payment["id"]),
            metadata={
                "debt_id": payment.debt_id,
                "amount": float(payment.amount_paid),
                "payment_method": payment_method,
                "transaction_reference": payment_ref,
            },
        )

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
def create_payment_plan(plan: PaymentPlanCreate, db=Depends(get_db), user=Depends(require_auth)):
    """
    Creates a new payment plan and generates its schedule.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    from app.core.audit import write_audit_log
    try:
        # 1. Generate Schedule to identify Down Payment
        schedule = generate_payment_schedule(
            plan.total_settlement_amount, 
            plan.down_payment_amount, 
            plan.installment_count, 
            plan.frequency, 
            plan.start_date
        )

        # 2. Identify Down Payment (if any)
        dp_item = next((item for item in schedule if item.get('type') == 'Down Payment'), None)

        # 3. Fetch debtor for AVS/customer metadata
        cursor.execute("""
            SELECT 
                dr.first_name, dr.last_name, dr.email, dr.address_1, dr.address_2, dr.city, dr.state, dr.zip_code, dr.phone,
                d.client_reference_number
            FROM debts d
            JOIN debtors dr ON d.debtor_id = dr.id
            WHERE d.id = %s
        """, (plan.debt_id,))
        debtor = cursor.fetchone()

        full_name = plan.cardholder_name.strip() if plan.cardholder_name else ""
        name_parts = [part for part in full_name.split(" ") if part]
        fallback_first = name_parts[0] if name_parts else ""
        fallback_last = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        customer_data = {
            "first_name": debtor.get("first_name") if debtor else fallback_first,
            "last_name": debtor.get("last_name") if debtor else fallback_last,
            "email": debtor.get("email") if debtor else "",
            "custid": debtor.get("client_reference_number") if debtor else "",
            "address": plan.billing_address or (debtor.get("address_1") if debtor else ""),
            "address2": debtor.get("address_2") if debtor else "",
            "city": plan.billing_city or (debtor.get("city") if debtor else ""),
            "state": plan.billing_state or (debtor.get("state") if debtor else ""),
            "zip": plan.billing_zip or (debtor.get("zip_code") if debtor else ""),
            "phone": debtor.get("phone") if debtor else ""
        }

        # 4. Tokenization flow
        dp_result = None
        card_token = None
        if dp_item and dp_item['amount'] > 0:
            # Run Down Payment via payment_key and save card
            try:
                epay_resp = usa_epay.run_payment_key_sale(
                    payment_key=plan.payment_key,
                    amount=dp_item['amount'],
                    invoice=f"Debt-{plan.debt_id}-DP",
                    customer_data=customer_data,
                    stored_credential="installment",
                    save_card=True
                )
                card_token = epay_resp.get("saved_card_key")
                payment_ref = epay_resp.get("refnum", "USAePay Payment Key")
            except Exception as dp_err:
                print(f"Down payment failed: {dp_err}")
                raise HTTPException(status_code=400, detail=f"Down Payment Failed: {str(dp_err)}. Plan not created.")

            # Record Down Payment in internal ledger
            cursor.execute("""
                SELECT p.commission_percentage 
                FROM debts d 
                JOIN portfolios p ON d.portfolio_id = p.id 
                WHERE d.id = %s
            """, (plan.debt_id,))
            res = cursor.fetchone()
            commission_rate = res['commission_percentage'] if res else Decimal("30.0")
            split = calculate_split(dp_item['amount'], commission_rate)

            cursor.execute("""
            INSERT INTO payments (
                debt_id, amount_paid, agency_portion, client_portion,
                transaction_reference, scheduled_payment_id, payment_method,
                status, result_code, result, error_message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'paid', %s, %s, NULL)
            RETURNING id, timestamp
        """, (
            plan.debt_id, dp_item['amount'], split['agency_portion'], split['client_portion'],
            payment_ref, None, "payment_key", "A", "Approved"
        ))
            new_payment = cursor.fetchone()

            cursor.execute("""
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
            """, (
                dp_item['amount'], dp_item['amount'], dp_item['amount'], new_payment['id'],
                payment_ref, "payment_key", dp_item['amount'], plan.debt_id
            ))

            dp_result = {
                "payment_id": new_payment['id'],
                "ref_num": payment_ref,
                "amount": dp_item['amount'],
                "timestamp": new_payment['timestamp']
            }
        else:
            # No down payment; run a $1 verification sale to obtain a reusable token, then void it
            try:
                verify_resp = usa_epay.run_payment_key_sale(
                    payment_key=plan.payment_key,
                    amount=Decimal("1.00"),
                    invoice=f"Debt-{plan.debt_id}-VERIFY",
                    customer_data=customer_data,
                    stored_credential="installment",
                    save_card=True
                )
                card_token = verify_resp.get("saved_card_key")
                refnum = verify_resp.get("refnum")
                if not card_token:
                    raise Exception("Verification sale approved but no saved card token returned.")
                if refnum:
                    usa_epay.void_transaction(refnum)
                else:
                    raise Exception("Verification sale approved but refnum missing for void.")
            except Exception as auth_err:
                print(f"Tokenization verify failed: {auth_err}")
                raise HTTPException(status_code=400, detail=f"Card Tokenization Failed: {str(auth_err)}. Plan not created.")

        manager = TransactionManager(cursor)
        today_date = datetime.now().date()

        # 6. Insert Plan
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

        # 7. Insert Schedule
        today_ct = datetime.now(CT_TZ).date()
        for item in schedule:
            due_date = item['due_date'].date() if isinstance(item['due_date'], datetime) else item['due_date']
            status = 'pending'
            payment_id = None
            transaction_reference = None
            payment_method = None
            processed_at = None
            last_result_code = None
            last_result = None
            next_attempt_at = None

            # If this was the DP we just ran, mark it paid
            if item.get('type') == 'Down Payment' and dp_result:
                status = 'paid'
                payment_id = dp_result['payment_id']
                transaction_reference = dp_result['ref_num']
                payment_method = 'payment_key'
                processed_at = dp_result['timestamp']
                last_result_code = "A"
                last_result = "Approved"
            elif status == 'pending' and due_date > today_ct:
                next_attempt_at = compute_next_attempt_at(due_date)

            cursor.execute("""
                INSERT INTO scheduled_payments (
                    plan_id, amount, due_date, status, actual_payment_id,
                    transaction_reference, payment_method, processed_at,
                    attempt_count, next_attempt_at, last_result_code, last_result
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                plan_id, item['amount'], item['due_date'], status, payment_id,
                transaction_reference, payment_method, processed_at,
                0, next_attempt_at, last_result_code, last_result
            ))
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
        
        write_audit_log(
            cursor,
            actor_id=user.get("sub"),
            action="payment_plan.created",
            entity_type="payment_plan",
            entity_id=str(plan_id),
            metadata={
                "debt_id": plan.debt_id,
                "total_settlement_amount": float(plan.total_settlement_amount),
                "down_payment_amount": float(plan.down_payment_amount),
                "installment_count": plan.installment_count,
                "frequency": plan.frequency,
                "start_date": str(plan.start_date),
                "has_down_payment": bool(dp_result),
            },
        )

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
    except Exception as e:
        print(f"Error in get_debt_plans for debt {debt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.get("/payment-plans/{plan_id}/schedule", response_model=List[ScheduledPaymentResponse])
def get_plan_schedule(plan_id: int, db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            """
            SELECT *
            FROM scheduled_payments
            WHERE plan_id = %s
            ORDER BY due_date ASC, id ASC
            """,
            (plan_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()

@router.get("/debug/epay-account")
def debug_epay_account():
    if os.getenv("ENABLE_DEBUG_ENDPOINTS", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Not found")

    try:
        account = usa_epay.fetch_account()
        api_key = os.getenv("USA_EPAY_API_KEY", "")
        return {
            "base_url": usa_epay.base_url,
            "api_key_suffix": api_key[-6:] if api_key else None,
            "account": account
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

@router.post("/debug/run-next-installment")
def debug_run_next_installment(plan_id: int, db=Depends(get_db)):
    if os.getenv("ENABLE_DEBUG_ENDPOINTS", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Not found")

    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT sp.id, sp.amount, sp.status, sp.due_date, sp.attempt_count, pp.debt_id, pp.card_token
            FROM scheduled_payments sp
            JOIN payment_plans pp ON sp.plan_id = pp.id
            WHERE sp.plan_id = %s AND sp.status = 'pending'
            ORDER BY sp.due_date ASC
            LIMIT 1
        """, (plan_id,))
        scheduled = cursor.fetchone()

        if not scheduled:
            raise HTTPException(status_code=404, detail="No pending scheduled payments found")
        if not scheduled.get("card_token"):
            raise HTTPException(status_code=400, detail="Plan has no card token")

        manager = TransactionManager(cursor)
        attempt_count = (scheduled.get('attempt_count') or 0) + 1
        result = manager.execute_payment(
            debt_id=scheduled['debt_id'],
            amount=scheduled['amount'],
            card_token=scheduled['card_token'],
            scheduled_payment_id=scheduled['id'],
            attempt_count=attempt_count
        )
        db.commit()
        return {
            "scheduled_payment_id": scheduled['id'],
            "due_date": str(scheduled['due_date']),
            "result": result
        }
    except HTTPException as he:
        raise he
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        cursor.close()

@router.post("/payments/scheduled/{payment_id}/execute")
def execute_scheduled_payment(payment_id: int, db=Depends(get_db), user=Depends(require_auth)):
    """
    Manually executes a scheduled payment early.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    from app.core.audit import write_audit_log
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
        attempt_count = (payment.get('attempt_count') or 0) + 1
        result = manager.execute_payment(
            debt_id=payment['debt_id'],
            amount=payment['amount'],
            card_token=payment['card_token'],
            scheduled_payment_id=payment_id,
            attempt_count=attempt_count
        )
        
        write_audit_log(
            cursor,
            actor_id=user.get("sub"),
            action="scheduled_payment.executed",
            entity_type="scheduled_payment",
            entity_id=str(payment_id),
            metadata={
                "debt_id": payment.get("debt_id"),
                "amount": float(payment.get("amount") or 0),
                "payment_id": result.get("payment_id"),
                "status": result.get("status"),
            },
        )

        db.commit()
        if result.get("status") == "declined":
            raise HTTPException(status_code=400, detail=result.get("result") or "Payment Declined")
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
def get_admin_payments(
    status: Optional[str] = None,
    days: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Admin view for payment management.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT 
                sp.id, sp.amount, sp.due_date, sp.status, sp.created_at,
                sp.next_attempt_at, sp.attempt_count, sp.last_result, sp.last_result_code, sp.last_decline_reason,
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

        if start_date or end_date:
            if start_date:
                query += " AND sp.due_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND sp.due_date <= %s"
                params.append(end_date)
        else:
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
def run_one_off_payment(debt_id: int, amount: Decimal, db=Depends(get_db), user=Depends(require_auth)):
    """
    Runs a manual payment using the most recent card token for this debt.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    from app.core.audit import write_audit_log
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
        
        write_audit_log(
            cursor,
            actor_id=user.get("sub"),
            action="payment.one_off.executed",
            entity_type="payment",
            entity_id=str(result.get("payment_id")),
            metadata={
                "debt_id": debt_id,
                "amount": float(amount),
                "status": result.get("status"),
            },
        )

        db.commit()
        if result.get("status") == "declined":
            raise HTTPException(status_code=400, detail=result.get("result") or "Payment Declined")
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()


@router.get("/reports/daily-money")
def get_daily_money_report(date: Optional[str] = None, db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now(CT_TZ).date()

        start_utc, end_utc = _ct_day_bounds(target_date)
        month_end = _month_end(target_date)

        # Green: posted today, not scheduled previously
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount_paid), 0) AS total, COUNT(*) AS count
            FROM payments
            WHERE status = 'paid'
              AND scheduled_payment_id IS NULL
              AND timestamp >= %s AND timestamp < %s
            """,
            (start_utc, end_utc)
        )
        green = cursor.fetchone()

        # Red: scheduled today, due on/before month end
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
            FROM scheduled_payments
            WHERE status IN ('pending', 'retrying')
              AND created_at >= %s AND created_at < %s
              AND due_date >= %s AND due_date <= %s
            """,
            (start_utc, end_utc, target_date, month_end)
        )
        red = cursor.fetchone()

        # Blue: scheduled today, due after month end
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
            FROM scheduled_payments
            WHERE status IN ('pending', 'retrying')
              AND created_at >= %s AND created_at < %s
              AND due_date > %s
            """,
            (start_utc, end_utc, month_end)
        )
        blue = cursor.fetchone()

        return {
            "date": target_date.isoformat(),
            "green": {"total": float(green['total']), "count": green['count']},
            "red": {"total": float(red['total']), "count": red['count']},
            "blue": {"total": float(blue['total']), "count": blue['count']},
        }
    finally:
        cursor.close()


@router.get("/reports/liquidation")
def get_liquidation_report(portfolio_id: Optional[int] = None, db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        params = []
        portfolio_filter = ""
        if portfolio_id:
            portfolio_filter = "WHERE p.id = %s"
            params.append(portfolio_id)

        cursor.execute(
            f"""
            WITH fv AS (
                SELECT p.id AS portfolio_id, p.name,
                       COALESCE(SUM(d.face_value), 0) AS face_value
                FROM portfolios p
                LEFT JOIN debts d ON d.portfolio_id = p.id
                {portfolio_filter}
                GROUP BY p.id, p.name
            ), posted AS (
                SELECT d.portfolio_id,
                       COALESCE(SUM(p.amount_paid), 0) AS posted_total
                FROM payments p
                JOIN debts d ON d.id = p.debt_id
                WHERE p.status = 'paid'
                GROUP BY d.portfolio_id
            ), pending AS (
                SELECT d.portfolio_id,
                       COALESCE(SUM(sp.amount), 0) AS pending_total
                FROM scheduled_payments sp
                JOIN payment_plans pp ON pp.id = sp.plan_id
                JOIN debts d ON d.id = pp.debt_id
                WHERE sp.status IN ('pending', 'retrying')
                GROUP BY d.portfolio_id
            )
            SELECT fv.portfolio_id, fv.name,
                   fv.face_value,
                   COALESCE(posted.posted_total, 0) AS posted_total,
                   COALESCE(pending.pending_total, 0) AS pending_total
            FROM fv
            LEFT JOIN posted ON posted.portfolio_id = fv.portfolio_id
            LEFT JOIN pending ON pending.portfolio_id = fv.portfolio_id
            ORDER BY fv.name ASC
            """,
            tuple(params)
        )
        rows = cursor.fetchall()

        results = []
        for row in rows:
            face_value = float(row['face_value']) if row['face_value'] else 0.0
            posted_total = float(row['posted_total']) if row['posted_total'] else 0.0
            pending_total = float(row['pending_total']) if row['pending_total'] else 0.0
            posted_liq = (posted_total / face_value) if face_value else 0.0
            total_liq = ((posted_total + pending_total) / face_value) if face_value else 0.0

            results.append({
                "portfolio_id": row['portfolio_id'],
                "name": row['name'],
                "face_value": face_value,
                "posted_total": posted_total,
                "pending_total": pending_total,
                "posted_liquidation": posted_liq,
                "total_liquidation": total_liq,
            })

        return results if not portfolio_id else (results[0] if results else {})
    finally:
        cursor.close()



