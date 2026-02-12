from app.core.database import get_db_connection
conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'interaction_logs'")
print(cur.fetchall())
conn.close()
