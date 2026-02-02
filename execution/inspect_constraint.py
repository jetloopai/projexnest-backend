import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'proposal_templates_template_type_check';")
    row = cur.fetchone()
    if row:
        with open("constraint.log", "w", encoding="utf-8") as f:
            f.write(row[0])
        print("Written to constraint.log")
    else:
        print("Constraint not found")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
