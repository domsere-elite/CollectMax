import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()
    print("Tables in Supabase public schema:")
    for table in tables:
        print(f" - {table[0]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
