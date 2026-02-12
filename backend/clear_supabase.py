import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
    conn.autocommit = True
    cur = conn.cursor()
    
    # Drop public schema and recreate it
    print("Dropping existing public schema in Supabase...")
    cur.execute("DROP SCHEMA public CASCADE")
    cur.execute("CREATE SCHEMA public")
    cur.execute("GRANT ALL ON SCHEMA public TO postgres")
    cur.execute("GRANT ALL ON SCHEMA public TO public")
    
    print("✓ Schema cleared.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
