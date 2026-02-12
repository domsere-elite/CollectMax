from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Shared Properties
# Shared Properties
class DebtorBase(BaseModel):
    first_name: str
    last_name: str
    dob: Optional[str] = None 
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: str
    phone: Optional[str] = None
    mobile_consent: bool = False
    email: Optional[str] = None

class DebtBase(BaseModel):
    client_reference_number: Optional[str] = None
    original_account_number: str
    original_creditor: Optional[str] = None
    current_creditor: Optional[str] = None
    date_opened: Optional[str] = None
    charge_off_date: Optional[str] = None
    principal_balance: Optional[Decimal] = None
    fees_costs: Optional[Decimal] = None
    amount_due: Decimal
    last_payment_date: Optional[str] = None
    last_payment_amount: Optional[Decimal] = None
    total_paid_amount: Decimal = Decimal("0.00")

# Request Models
class InteractionCreate(BaseModel):
    debt_id: int
    action_type: str # 'Call', 'Email', 'SMS'
    notes: Optional[str] = None

class EmailTemplateSend(BaseModel):
    debt_id: int
    template_id: str

class DebtorEmailUpdate(BaseModel):
    email: str

class ValidationNoticeSend(BaseModel):
    debt_id: int
    pdf_url: str

class PaymentCreate(BaseModel):
    debt_id: int
    amount_paid: Decimal

class PaymentPlanCreate(BaseModel):
    debt_id: int
    total_settlement_amount: Decimal
    is_settlement: bool = True
    down_payment_amount: Decimal = Decimal("0.00")
    installment_count: int
    frequency: str # 'weekly', 'bi-weekly', 'monthly'
    start_date: datetime

    # Payment Key (Pay.js token)
    payment_key: str
    cardholder_name: str
    
    # Billing Address
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_zip: Optional[str] = None

class PaymentPlanResponse(BaseModel):
    id: int
    debt_id: int
    total_settlement_amount: Decimal
    is_settlement: bool
    down_payment_amount: Decimal
    installment_count: int
    frequency: str
    start_date: datetime
    status: str
    created_at: datetime
    
    # Enhanced Transaction Feedback
    down_payment_status: Optional[str] = None
    dp_reference: Optional[str] = None

    class Config:
        from_attributes = True

class ScheduledPaymentResponse(BaseModel):
    id: int
    amount: Decimal
    due_date: datetime
    status: str
    actual_payment_id: Optional[int] = None
    processed_at: Optional[datetime] = None
    transaction_reference: Optional[str] = None
    payment_method: Optional[str] = None
    attempt_count: Optional[int] = None
    next_attempt_at: Optional[datetime] = None
    last_result_code: Optional[str] = None
    last_result: Optional[str] = None
    last_decline_reason: Optional[str] = None
    last_error: Optional[str] = None

    class Config:
        from_attributes = True

# Response Models
class DebtorResponse(DebtorBase):
    id: str # UUID
    ssn_hash: str
    do_not_contact: bool

    class Config:
        from_attributes = True

class DebtResponse(DebtBase):
    id: int
    status: str
    debtor: DebtorResponse 

    class Config:
        from_attributes = True

class PaymentResponse(BaseModel):
    id: int
    amount_paid: Decimal
    agency_portion: Decimal
    client_portion: Decimal
    timestamp: datetime
    transaction_reference: Optional[str] = None
    scheduled_payment_id: Optional[int] = None
    payment_method: Optional[str] = None
    status: Optional[str] = None
    result_code: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
