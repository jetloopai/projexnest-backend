import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

email = "admin@example.com"
password = "TestPassword123!"

try:
    print(f"Creating user {email}...")
    # Use admin.create_user to bypass signup check
    res = supabase.auth.admin.create_user({
        "email": email, 
        "password": password,
        "email_confirm": True
    })
    
    if res.user:
        print(f"User Created: {res.user.id}")
        with open("user_id.txt", "w") as f:
            f.write(res.user.id)
    else:
        # If user already exists, maybe try sign in
        print("User might already exist, trying sign in...")
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if res.user:
             print(f"User Found: {res.user.id}")
             with open("user_id.txt", "w") as f:
                f.write(res.user.id)
        else:
            print("Failed to get user.")
except Exception as e:
    print(f"Error: {e}")
