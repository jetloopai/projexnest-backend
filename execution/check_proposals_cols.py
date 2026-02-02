import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'proposals'
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("=== PROPOSALS COLUMNS ===")
for col in cols:
    print(f"  {col[0]}")

cur.close()
conn.close()
