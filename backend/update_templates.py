
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
    cur = conn.cursor()

    # Deprecate old one
    print("Deprecating ID 2 (Old Validation Notice)...")
    cur.execute("UPDATE email_templates SET name = 'Validation Notice (Deprecated-Broken)' WHERE id = 2")

    # Rename working one
    print("Renaming ID 1 (Agent Email Template) to Validation Notice...")
    cur.execute("UPDATE email_templates SET name = 'Validation Notice', description = 'Primary validation notice (formerly Agent Template)' WHERE id = 1")

    conn.commit()
    print("Updates committed successfully.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
