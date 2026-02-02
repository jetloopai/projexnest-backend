import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
FIX_FILE = os.path.join(os.path.dirname(__file__), 'fix_rls.sql')

def run_fix():
    if not DB_URL:
        print("Error: DATABASE_URL is not set.")
        return

    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("Reading fix_rls.sql...")
        with open(FIX_FILE, 'r') as f:
            fix_sql = f.read()
            
        print("Applying fix...")
        cur.execute(fix_sql)
        conn.commit()
        
        print("Success! Database fix applied.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error applying fix: {e}")

if __name__ == "__main__":
    run_fix()
