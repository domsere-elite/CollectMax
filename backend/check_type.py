import psycopg2
from psycopg2.extras import RealDictCursor

try:
    conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT charge_off_date FROM debts WHERE id = 5')
    r = cur.fetchone()
    print(f"Type: {type(r.get('charge_off_date'))} | Value: {r.get('charge_off_date')}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
