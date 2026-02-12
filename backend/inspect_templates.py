
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

output_file = "templates_output.txt"

try:
    with open(output_file, "w", encoding="utf-8") as f:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
        cur = conn.cursor(cursor_factory=RealDictCursor)

        f.write("--- ALL EMAIL TEMPLATES ---\n")
        cur.execute("SELECT id, name, template_id, description FROM email_templates ORDER BY id")
        rows = cur.fetchall()
        for row in rows:
            f.write(f"ID: {row['id']} | Name: {row['name']} | SG_ID: {row['template_id']}\n")
            if row['description']:
                f.write(f"  Desc: {row['description']}\n")
            f.write("-" * 30 + "\n")

        cur.close()
        conn.close()
        f.write("\nDONE\n")
    print(f"Output written to {output_file}")

except Exception as e:
    print(f"Error: {e}")
