import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
    cur = conn.cursor()
    
    tables = [
        'debts', 'debtors', 'portfolios', 'clients', 'payments', 
        'payment_plans', 'scheduled_payments', 'interaction_logs', 
        'email_templates', 'email_logs', 'campaigns', 'campaign_recipients'
    ]
    
    print("Record counts in Supabase:")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f" - {table}: {count}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
