import psycopg2
from datetime import date

conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
cur = conn.cursor()

today = date.today()
print(f"Checking for events on {today}:")

cur.execute("SELECT COUNT(*) FROM campaigns WHERE created_at >= %s", (today,))
print(f"Campaigns created today: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM email_logs WHERE created_at >= %s", (today,))
print(f"Emails logged today: {cur.fetchone()[0]}")

cur.execute("SELECT id, status, error_message FROM email_logs WHERE created_at >= %s ORDER BY created_at DESC LIMIT 5", (today,))
logs = cur.fetchall()
for log in logs:
    print(f"ID: {log[0]}, Status: {log[1]}, Error: {log[2]}")

conn.close()
