#!/usr/bin/env python3
"""
Apply ALL pending database migrations to local PostgreSQL.
"""
import sys
import os
import glob

# Add backend directory to sys.path to import get_db_connection
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import get_db_connection

def apply_migration(migration_file, cursor):
    """Apply a single SQL migration file."""
    print(f"Applying migration: {os.path.basename(migration_file)}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        cursor.execute(sql)
        print(f"✅ Applied: {os.path.basename(migration_file)}")
        return True
    except Exception as e:
        print(f"❌ Error applying {os.path.basename(migration_file)}: {e}")
        return False

def main():
    conn = get_db_connection()
    conn.autocommit = False # Use transactions
    cursor = conn.cursor()
    
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    
    # Get all .sql files and sort them to run in order
    migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
    
    print(f"Found {len(migration_files)} migration files.")
    
    try:
        for migration_file in migration_files:
            # Skip the ones we know are potentially conflicting or already handled if needed
            # For now, apply all sorted by name
            if not apply_migration(migration_file, cursor):
                print("Rolling back changes...")
                conn.rollback()
                return

        conn.commit()
        print("\n🎉 All migrations applied successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Critical Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
