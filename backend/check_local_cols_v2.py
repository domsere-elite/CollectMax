from app.core.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

def get_cols(table):
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' ORDER BY column_name")
    return [r[0] for r in cur.fetchall()]

tables = ['debtors', 'debts', 'portfolios', 'clients']
for t in tables:
    cols = get_cols(t)
    print(f"Table: {t}")
    for c in cols:
        print(f"  - {c}")

conn.close()
