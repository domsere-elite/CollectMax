import psycopg2

conn = psycopg2.connect(host='localhost', database='collectsecure', user='postgres', password='abc123', port='5433')
cur = conn.cursor()

debt_id = 5
cur.execute("SELECT debtor_id FROM debts WHERE id = %s", (debt_id,))
res = cur.fetchone()
if res:
    did = res[0]
    print(f"Debt 5 debtor_id: {did}")
    cur.execute("SELECT count(*) FROM debtors WHERE id = %s", (did,))
    print(f"Debtor count for {did}: {cur.fetchone()[0]}")
else:
    print("Debt 5 not found")

conn.close()
