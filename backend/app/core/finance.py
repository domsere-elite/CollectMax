from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def calculate_split(payment_amount: Decimal, commission_rate: Decimal):
    # ... (existing code)
    if commission_rate < 0 or commission_rate > 100:
        raise ValueError("Invalid commission rate")

    rate_factor = commission_rate / Decimal(100)
    
    agency_fee = payment_amount * rate_factor
    client_remit = payment_amount - agency_fee
    
    # Rounding to 2 decimal places
    agency_fee = agency_fee.quantize(Decimal("0.01"))
    client_remit = client_remit.quantize(Decimal("0.01"))
    
    return {
        "agency_portion": agency_fee,
        "client_portion": client_remit
    }

def generate_payment_schedule(total_amount: Decimal, down_payment: Decimal, installment_count: int, frequency: str, start_date: datetime):
    """
    Generates a list of (date, amount) tuples for a payment plan.
    Ensures that the sum of installments equals exactly (total_amount - down_payment).
    """
    schedule = []
    current_date = start_date
    
    # Prepend Down Payment if exists
    if down_payment > 0:
        schedule.append({
            "due_date": current_date,
            "amount": down_payment.quantize(Decimal("0.01")),
            "type": "Down Payment"
        })
        # Advance the date for the first installment
        if frequency == 'weekly':
            current_date += timedelta(weeks=1)
        elif frequency == 'bi-weekly':
            current_date += timedelta(weeks=2)
        elif frequency == 'monthly':
            current_date += relativedelta(months=1)

    remaining_balance = total_amount - down_payment
    if installment_count <= 0:
        return schedule

    base_payment = (remaining_balance / installment_count).quantize(Decimal("0.01"))
    
    for i in range(installment_count):
        # Last payment adjusts for rounding differences
        if i == installment_count - 1:
            payment_amount = remaining_balance - (base_payment * (installment_count - 1))
        else:
            payment_amount = base_payment
            
        schedule.append({
            "due_date": current_date,
            "amount": payment_amount,
            "type": "Installment"
        })
        
        # Increment date based on frequency
        if frequency == 'weekly':
            current_date += timedelta(weeks=1)
        elif frequency == 'bi-weekly':
            current_date += timedelta(weeks=2)
        elif frequency == 'monthly':
            current_date += relativedelta(months=1)
            
    return schedule
