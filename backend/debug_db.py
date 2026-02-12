import os
import sys
from app.core.database import get_db_connection
from psycopg2.extras import RealDictCursor

# Mock env vars if needed
os.environ['DATABASE_URL'] = "postgresql://postgres:postgres@localhost:5432/collectmax"

def debug_debt(debt_id):
    import sys
    with open("debug_output.txt", "a") as f:
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            f.write(f"--- Debugging Debt {debt_id} ---\n")
            
            # 1. Check direct columns
            cur.execute("SELECT id, original_creditor, current_creditor, portfolio_id FROM debts WHERE id = %s", (debt_id,))
            debt = cur.fetchone()
            
            if not debt:
                f.write("Debt not found\n")
                return

            f.write(f"Original Creditor: '{debt['original_creditor']}'\n")
            f.write(f"Current Creditor (Raw DB): '{debt['current_creditor']}'\n")
            f.write(f"Portfolio ID: {debt['portfolio_id']}\n")
            
            # 2. Check Portfolio/Client
            client_name = None
            if debt['portfolio_id']:
                cur.execute("""
                    SELECT p.name as portfolio_name, c.name as client_name 
                    FROM portfolios p 
                    LEFT JOIN clients c ON p.client_id = c.id 
                    WHERE p.id = %s
                """, (debt['portfolio_id'],))
                res = cur.fetchone()
                f.write(f"Portfolio Name: '{res['portfolio_name']}'\n")
                f.write(f"Client Name: '{res['client_name']}'\n")
                client_name = res['client_name']
            
            # 3. Simulate Logic
            # Emulate NULLIF(current_creditor, '')
            raw_curr = debt['current_creditor']
            if raw_curr == '': raw_curr = None
            
            effective = raw_curr if raw_curr else client_name
            f.write(f"Effective Creditor (Python Logic): '{effective}'\n")

        except Exception as e:
            f.write(f"Error: {e}\n")
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    for i in range(1, 6):
        debug_debt(i)
