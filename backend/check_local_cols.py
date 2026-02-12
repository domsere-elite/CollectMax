from app.core.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

def get_cols(table):
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
    return [r[0] for r in cur.fetchall()]

tables = ['debtors', 'debts', 'portfolios', 'clients']
for t in tables:
    print(f"{t}: {get_cols(t)}")

conn.close()
