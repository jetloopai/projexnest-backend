import httpx
import sys

try:
    print("Checking /workflow/clients endpoint...")
    resp = httpx.get("http://localhost:8000/workflow/clients?org_id=test")
    print(f"Status: {resp.status_code}")
    if resp.status_code != 404: # 404 means route doesn't exist (old version)
        print("SUCCESS: Endpoint exists!")
    else:
        print("FAILURE: Endpoint 404 (Old version still running?)")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: Cloud not connect. {e}")
    sys.exit(1)
