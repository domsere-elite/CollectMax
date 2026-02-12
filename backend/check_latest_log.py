import psycopg2
from psycopg2.extras import RealDictCursor
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT COUNT(*) FROM email_logs")
    print(f"Total email logs: {cur.fetchone()['count']}")
    
    cur.execute("SELECT * FROM email_logs ORDER BY created_at DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        print("LATEST EMAIL LOG:")
        for k, v in row.items():
            print(f"  {k}: {v}")
    else:
        print("No logs found.")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
