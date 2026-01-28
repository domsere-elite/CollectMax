import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Mock DB Configuration for Dev/Scaffold (would use robust env vars in prod)
# Mock DB Configuration for Dev/Scaffold (would use robust env vars in prod)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "collectsecure")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "abc123")
DB_PORT = os.getenv("DB_PORT", "5433")

def get_db_connection():
    """
    Establishes a connection to the database.
    In a real AlloyDB setup, this would use a connection pool (e.g., psycopg2.pool.SimpleConnectionPool)
    """
    try:
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
        # Retrying or failing gracefully would happen here
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
