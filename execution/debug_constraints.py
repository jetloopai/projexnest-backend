import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

output = []

# Check the template_type constraint
cur.execute("""
    SELECT conname, pg_get_constraintdef(oid) 
    FROM pg_constraint 
    WHERE conname LIKE '%template%'
""")
constraints = cur.fetchall()
output.append("=== TEMPLATE CONSTRAINTS ===")
for c in constraints:
    output.append(f"  {c[0]}: {c[1]}")

# Also check columns of proposal_templates
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name = 'proposal_templates'
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
output.append("\n=== PROPOSAL_TEMPLATES COLUMNS ===")
for col in cols:
    output.append(f"  {col[0]} ({col[1]}), nullable={col[2]}, default={col[3]}")

cur.close()
conn.close()

with open("constraint_log.txt", "w") as f:
    f.write("\n".join(output))
print("Wrote to constraint_log.txt")
