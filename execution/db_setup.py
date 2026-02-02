import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'schema.sql')

def run_migration():
    if not DB_URL:
        print("Error: DATABASE_URL is not set in .env")
        print("Please add your Supabase Connection String to .env")
        return

    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("Reading schema.sql...")
        with open(SCHEMA_FILE, 'r') as f:
            schema_sql = f.read()
            
        print("Applying schema...")
        cur.execute(schema_sql)
        conn.commit()
        
        print("Success! Schema applied.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == "__main__":
    if not DB_URL:
        print("Error: DATABASE_URL is not set in .env")
    else:
        # Diagnostic check (masking password)
        try:
            from urllib.parse import urlparse
            result = urlparse(DB_URL)
            print(f"Debug: Scheme={result.scheme}, Username={result.username}, Host={result.hostname}, Port={result.port}, Path={result.path}")
            if result.password:
                print("Debug: Password is present (length: " + str(len(result.password)) + ")")
                special_chars = ['@', ':', '/', '?', '#']
                if any(char in result.password for char in special_chars):
                     print("WARNING: Password contains special characters that might break the connection string. Please URL-encode them.")
            else:
                print("Debug: No password found in connection string!")
        except Exception as e:
            print(f"Debug: Error parsing URL: {e}")

    run_migration()
