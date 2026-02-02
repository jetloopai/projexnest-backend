import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

print("=== ORGANIZATIONS ===")
orgs = supabase.table("organizations").select("*").execute()
for org in orgs.data:
    print(f"  {org['id']} - {org['name']}")

if not orgs.data:
    print("  (No organizations found!)")

print("\n=== ORG_MEMBERSHIPS ===")
memberships = supabase.table("org_memberships").select("*").execute()
for m in memberships.data:
    print(f"  User: {m['user_id']} -> Org: {m['org_id']} (Role: {m['role']})")

if not memberships.data:
    print("  (No memberships found!)")

print("\n=== AUTH.USERS ===")
# Use admin API to list users
users = supabase.auth.admin.list_users()
for u in users:
    print(f"  {u.id} - {u.email}")
