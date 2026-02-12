import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
    cur = conn.cursor()
    
    print("Checking most recent campaigns:")
    cur.execute("SELECT id, name, status, sent_count, failed_count, created_at FROM campaigns ORDER BY created_at DESC LIMIT 5")
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Name: {row[1]}, Status: {row[2]}, Sent: {row[3]}, Failed: {row[4]}, Created: {row[5]}")

    print("\nChecking most recent email logs:")
    cur.execute("SELECT id, email_to, subject, status, error_message, created_at FROM email_logs ORDER BY created_at DESC LIMIT 5")
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, To: {row[1]}, Subject: {row[2]}, Status: {row[3]}, Error: {row[4]}, Created: {row[5]}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
