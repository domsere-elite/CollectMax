import psycopg2

try:
    conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
    cur = conn.cursor()
    
    print("Creating audit_logs table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            actor_id VARCHAR(255),
            action VARCHAR(255) NOT NULL,
            entity_type VARCHAR(100) NOT NULL,
            entity_id VARCHAR(255) NOT NULL,
            before JSONB DEFAULT '{}'::jsonb,
            after JSONB DEFAULT '{}'::jsonb,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    print("✓ audit_logs table created.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
