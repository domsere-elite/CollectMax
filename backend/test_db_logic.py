import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = "postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

try:
    # Find a valid debt with a debtor
    cur.execute("SELECT d.id FROM debts d JOIN debtors dr ON d.debtor_id = dr.id LIMIT 1")
    res = cur.fetchone()
    if not res:
        print("No valid debt/debtor pair found")
        exit()
    debt_id = res['id']
    new_email = "test@example.com"
    print(f"Testing with Debt ID: {debt_id}")

    cur.execute("SELECT dr.id AS debtor_id FROM debts d JOIN debtors dr ON d.debtor_id = dr.id WHERE d.id = %s", (debt_id,))
    record = cur.fetchone()
    print(f"Record: {record}")
    
    if record:
        cur.execute("SELECT email FROM debtors WHERE id = %s", (record["debtor_id"],))
        existing = cur.fetchone()
        previous_email = existing.get("email") if existing else None
        print(f"Previous Email: {previous_email}")
        
        cur.execute("UPDATE debtors SET email = %s WHERE id = %s", (new_email, record["debtor_id"]))
        print("Updated debtors")
        
        # Explicit type cast for enum
        cur.execute("INSERT INTO interaction_logs (debt_id, action_type, notes) VALUES (%s, %s::action_type, %s)", (debt_id, "Other", f"Email updated from '{previous_email}' to '{new_email}'"))
        print("Logged interaction")
        
        conn.commit()
        print("Committed")
    else:
        print("Debt not found")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
