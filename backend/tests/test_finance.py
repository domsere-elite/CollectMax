import pytest
from decimal import Decimal
from datetime import datetime
from app.core.finance import calculate_split, generate_payment_schedule

def test_calculate_split_normal():
    # $100 payment, 30% commission
    # Agency: $30, Client: $70
    result = calculate_split(Decimal("100.00"), Decimal("30.0"))
    assert result["agency_portion"] == Decimal("30.00")
    assert result["client_portion"] == Decimal("70.00")

def test_calculate_split_complex():
    # $150.50 payment, 12.5% commission
    result = calculate_split(Decimal("150.50"), Decimal("12.5"))
    assert result["agency_portion"] == Decimal("18.81")
    assert result["client_portion"] == Decimal("131.69")

def test_generate_payment_schedule_with_down_payment():
    total = Decimal("1000.00")
    down = Decimal("100.00")
    installments = 3
    start = datetime(2026, 1, 1)
    
    schedule = generate_payment_schedule(total, down, installments, "monthly", start)
    
    # Total payments = 1 (DP) + 3 (Inst) = 4
    assert len(schedule) == 4
    
    # First payment should be the Down Payment
    assert schedule[0]["type"] == "Down Payment"
    assert schedule[0]["amount"] == Decimal("100.00")
    assert schedule[0]["due_date"] == start
    
    # Second payment should be the first installment, 1 month later
    assert schedule[1]["type"] == "Installment"
    assert schedule[1]["due_date"] == datetime(2026, 2, 1)
    # Remaining 900 / 3 = 300
    assert schedule[1]["amount"] == Decimal("300.00")
    
    # Verify total sum
    total_scheduled = sum(item["amount"] for item in schedule)
    assert total_scheduled == total
