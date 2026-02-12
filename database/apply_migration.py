#!/usr/bin/env python3
"""
Apply database migration to local PostgreSQL.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import get_db_connection

def apply_migration(migration_file):
    """Apply a SQL migration file to the database."""
    print(f"Applying migration: {migration_file}")
    
    # Read migration file
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Execute migration
        cursor.execute(sql)
        conn.commit()
        print("Migration applied successfully.")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('email_logs', 'email_templates')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        if tables:
            print("\nNew tables created:")
            for table in tables:
                print(f"   - {table[0]}")
        
        # Verify indexes were created
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname LIKE 'idx_%'
            ORDER BY indexname;
        """)
        
        indexes = cursor.fetchall()
        if indexes:
            print(f"\nIndexes created: {len(indexes)} total")
            print("   Sample indexes:")
            for idx in indexes[:5]:
                print(f"   - {idx[0]}")
            if len(indexes) > 5:
                print(f"   ... and {len(indexes) - 5} more")
        
    except Exception as e:
        conn.rollback()
        print(f"Error applying migration: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        migration_path = sys.argv[1]
    else:
        migration_path = os.path.join(
            os.path.dirname(__file__), 
            'migrations', 
            '20260206_campaigns.sql'
        )
    
    if not os.path.exists(migration_path):
        print(f"Migration file not found: {migration_path}")
        sys.exit(1)
    
    apply_migration(migration_path)
