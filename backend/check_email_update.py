from app.core.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Find the debt and email for account number 51554204
cur.execute("""
    SELECT d.id, d.original_account_number, dr.email 
    FROM debts d 
    JOIN debtors dr ON d.debtor_id = dr.id 
    WHERE d.original_account_number = '51554204'
""")

result = cur.fetchone()

if result:
    print(f"✓ Found account:")
    print(f"  Debt ID: {result[0]}")
    print(f"  Account Number: {result[1]}")
    print(f"  Current Email: {result[2]}")
    
    if result[2] == 'dominic@eliteportfoliomgt.com':
        print(f"\n✓ Email is correctly set to: dominic@eliteportfoliomgt.com")
    else:
        print(f"\n✗ Email is NOT set to dominic@eliteportfoliomgt.com")
        print(f"  Expected: dominic@eliteportfoliomgt.com")
        print(f"  Actual: {result[2]}")
else:
    print("✗ Account number 51554204 not found in database")

conn.close()
