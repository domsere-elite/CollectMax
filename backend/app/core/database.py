import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load variables from .env file explicitly
load_dotenv()

# DB Configuration - Supabase takes precedence
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "collectsecure")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "abc123")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_SSLMODE = os.getenv("DB_SSLMODE")

def get_db_connection():
    """
    Establishes a connection to the database.
    """
    try:
        if DATABASE_URL:
            conn = psycopg2.connect(
                DATABASE_URL,
                sslmode=DB_SSLMODE or "require"
            )
        else:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT
            )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to DB: {e}")
        raise e

def get_db():
    """
    Dependency for FastAPI routers to get a DB cursor.
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
