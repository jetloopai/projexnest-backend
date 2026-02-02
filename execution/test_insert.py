import os
import uuid
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

try:
    print(f"Attempting to insert into organizations using key starting with: {key[:10]}...")
    resp = supabase.table("organizations").insert({
        "id": str(uuid.uuid4()),
        "name": "Test Org"
    }).execute()
    print("Success!")
    print(resp.data)
except Exception as e:
    print("ERROR:")
    print(e)
    # Try to print response body if available
    if hasattr(e, 'response'):
        print("Response Content:")
        print(e.response.text())
