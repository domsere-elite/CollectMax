import psycopg2
from dotenv import load_dotenv
import os

# 1. Check Local (5433)
try:
    conn = psycopg2.connect(host="localhost", database="collectsecure", user="postgres", password="abc123", port="5433")
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM debts")
    print(f"Local (5433) Debts: {cur.fetchone()[0]}")
    conn.close()
except Exception as e:
    print(f"Local (5433) Error: {e}")

# 2. Check Supabase
load_dotenv()
supabase_url = os.getenv("SUPABASE_DB_URL")
if supabase_url:
    try:
        conn = psycopg2.connect(supabase_url, sslmode="require")
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM debts")
        print(f"Supabase Debts: {cur.fetchone()[0]}")
        conn.close()
    except Exception as e:
        print(f"Supabase Error: {e}")
else:
    print("Supabase URL not found in .env")
