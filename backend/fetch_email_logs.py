import psycopg2
from psycopg2.extras import RealDictCursor
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT * FROM email_logs ORDER BY created_at DESC LIMIT 10")
    rows = cur.fetchall()
    
    if not rows:
        print("No emails found in history.")
    else:
        for row in rows:
            print(f"ID: {row['id']} | To: {row['email_to']} | Status: {row['status']} | Error: {row['error_message']} | Time: {row['created_at']}")
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
