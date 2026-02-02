import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, email FROM auth.users LIMIT 5;")
    rows = cur.fetchall()
    with open("users.log", "w", encoding="utf-8") as f:
        f.write("Users:\n")
        for r in rows:
            line = f"{r[0]} - {r[1]}\n"
            print(line.strip())
            f.write(line)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
