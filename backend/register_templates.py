import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:tft*hut7jnv1hwq7CYV@db.pnzoyspjspdyrnpxtdpj.supabase.co:5432/postgres?sslmode=require')
    cur = conn.cursor()
    
    templates = [
        ("Agent Email Template", "d-2292ad4d40954a3a878f9389f638ceb1", "Primary agent email template"),
        ("Validation Notice", "d-af354e38605d46e093e9a5c531d8e13f", "FDCPA Validation Notice")
    ]
    
    for name, tid, desc in templates:
        cur.execute("SELECT id FROM email_templates WHERE template_id = %s", (tid,))
        if not cur.fetchone():
            print(f"Registering template: {name} ({tid})")
            cur.execute("""
                INSERT INTO email_templates (name, template_id, description)
                VALUES (%s, %s, %s)
            """, (name, tid, desc))
        else:
            print(f"Template {tid} already registered.")
    
    conn.commit()
    print("✓ Done.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
