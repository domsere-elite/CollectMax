
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

output_file = "email_debug.txt"

try:
    with open(output_file, "w", encoding="utf-8") as f:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
        cur = conn.cursor(cursor_factory=RealDictCursor)

        f.write("--- DEBT #5 INFO ---\n")
        cur.execute("""
            SELECT d.id, d.original_account_number, dr.first_name, dr.last_name, dr.email, dr.id as debtor_id
            FROM debts d 
            JOIN debtors dr ON d.debtor_id = dr.id 
            WHERE d.id = 5
        """)
        debt = cur.fetchone()
        if debt:
            f.write(f"Debt ID: {debt['id']}\n")
            f.write(f"Debtor Name: {debt['first_name']} {debt['last_name']}\n")
            f.write(f"Debtor Email: {debt['email']}\n")
            f.write(f"Debtor ID: {debt['debtor_id']}\n")
        else:
            f.write("Debt #5 NOT FOUND\n")

        f.write("\n--- LAST 5 EMAIL LOGS ---\n")
        cur.execute("""
            SELECT id, email_to, template_id, status, sendgrid_message_id, created_at, error_message
            FROM email_logs 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        logs = cur.fetchall()

        for log in logs:
            f.write(f"Log ID: {log['id']}\n")
            f.write(f"  To: {log['email_to']}\n")
            f.write(f"  Status: {log['status']}\n")
            f.write(f"  Template: {log['template_id']}\n")
            f.write(f"  SG Msg ID: {log['sendgrid_message_id']}\n")
            f.write(f"  Time: {log['created_at']}\n")
            if log['error_message']:
                f.write(f"  Error: {log['error_message']}\n")
            f.write("-" * 30 + "\n")

        cur.close()
        conn.close()
        f.write("\nDONE\n")
    print(f"Output written to {output_file}")

except Exception as e:
    print(f"Error: {e}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"SCRIPT ERROR: {e}")
