"""Check email_logs and verify what happened with recent sends."""
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=== Recent email_logs (last 10) ===")
cur.execute("""
    SELECT id, debt_id, email_to, status, sendgrid_message_id, 
           error_message, template_id, created_at 
    FROM email_logs ORDER BY created_at DESC LIMIT 10
""")
rows = cur.fetchall()
if not rows:
    print("  (no entries)")
for row in rows:
    print(f"  #{row['id']} | debt={row['debt_id']} | to={row['email_to']} | status={row['status']} | msgid={row['sendgrid_message_id']} | tmpl={row['template_id']} | err={row['error_message']} | at={row['created_at']}")

print("\n=== Debtor email for debt 5 ===")
cur.execute("SELECT d.id, dr.email, dr.first_name, dr.last_name FROM debts d JOIN debtors dr ON d.debtor_id=dr.id WHERE d.id=5")
r = cur.fetchone()
print(f"  Debt #{r['id']}: {r['first_name']} {r['last_name']} <{r['email']}>")

print("\n=== All email templates in DB ===")
cur.execute("SELECT id, name, template_id, description FROM email_templates")
for row in cur.fetchall():
    print(f"  #{row['id']} | name={row['name']} | sg_id={row['template_id']} | desc={row['description']}")

cur.close()
conn.close()
