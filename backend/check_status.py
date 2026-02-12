
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

output_file = "email_final_check.txt"

try:
    with open(output_file, "w", encoding="utf-8") as f:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
        cur = conn.cursor(cursor_factory=RealDictCursor)

        f.write("--- DEBTOR STATUS ---\n")
        cur.execute("""
            SELECT email, email_bounce_status, email_last_bounced_at, email_unsubscribed 
            FROM debtors 
            WHERE email = 'dominic@eliteportfoliomgt.com'
        """)
        debtor = cur.fetchone()
        f.write(f"Email: {debtor['email']}\n")
        f.write(f"Bounce Status: {debtor['email_bounce_status']}\n")
        f.write(f"Last Bounced: {debtor['email_last_bounced_at']}\n")
        f.write(f"Unsubscribed: {debtor['email_unsubscribed']}\n")

        f.write("\n--- TEMPLATE DETAILS ---\n")
        # Check the template used in the last log (d-af354e38605d46e093e9a5c531d8e13f)
        target_template_id = "d-af354e38605d46e093e9a5c531d8e13f"
        cur.execute("SELECT * FROM email_templates WHERE template_id = %s", (target_template_id,))
        tmpl = cur.fetchone()
        if tmpl:
            f.write(f"Template Name: {tmpl['name']}\n")
            f.write(f"Description: {tmpl['description']}\n")
            f.write(f"ID: {tmpl['template_id']}\n")
        else:
            f.write(f"Template {target_template_id} NOT FOUND in DB\n")

        cur.close()
        conn.close()
        f.write("\nDONE\n")
    print(f"Output written to {output_file}")

except Exception as e:
    print(f"Error: {e}")
