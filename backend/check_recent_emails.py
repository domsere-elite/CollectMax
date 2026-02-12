import psycopg2
from datetime import date, datetime

conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
cur = conn.cursor()

print(f"Current UTC time: {datetime.utcnow()}")
cur.execute("SELECT id, email_to, subject, status, error_message, created_at FROM email_logs WHERE created_at > NOW() - interval '1 hour' ORDER BY created_at DESC")
rows = cur.fetchall()

if not rows:
    print("No emails sent in the last hour.")
else:
    for row in rows:
        print(f"ID: {row[0]}, To: {row[1]}, Subject: {row[2]}, Status: {row[3]}, Error: {row[4]}, Time: {row[5]}")

conn.close()
