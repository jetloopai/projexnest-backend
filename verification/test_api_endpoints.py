from fastapi.testclient import TestClient
from orchestration.api_server import app
import uuid

client = TestClient(app)

# Helper config
# Using known good IDs from logs or generating new ones if RLS/Constraints allow
# We need a valid org_id. From seed log: "Creating Org: cd5ddbbc..."
# But to be safe, we'll try to find one or fail gracefully.
# Actually, the seed data created an org. Let's hardcode one from the logs if possible or fetch via script.
# For API testing, valid FKs matter. 
# We'll rely on the fact that RLS allows insertion if we are the "service role" (which the python script is).
# But the python script uses `get_client()` which uses `SUPABASE_SERVICE_KEY`.

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "ProjexNest Orchestrator Running. v1.1"}
    print("ROOT: OK")

def test_create_signing_link_mock():
    # We can test the route logic even if FKs fail, but 500 would be raised on FK error.
    # Let's try to hit the signing link endpoint with dummy valid UUIDs to see if it reaches the DB layer.
    
    payload = {
        "proposal_version_id": str(uuid.uuid4()), # Non-existent, likely to fail constraint
        "signer_email": "test@example.com"
    }
    
    # Expecting 500 due to FK violation, but checking that it reached that point
    response = client.post("/workflow/signing-links", json=payload)
    
    # If the server is running and logic works, it should try to insert and fail DB constraint.
    # 500 Internal Server Error is expected for unhandled DB exceptions in the mock code.
    if response.status_code == 200:
        print("SIGNING LINK: OK (Unexpected success with fake ID?)")
    elif response.status_code == 500:
        err = response.json().get("detail", "")
        if "violates foreign key constraint" in err or "violates not-null constraint" in err:
             print(f"SIGNING LINK: OK (Failed as expected at DB layer: {err[:50]}...)")
        else:
             print(f"SIGNING LINK: FAILED (Unknown 500: {err})")
    else:
        print(f"SIGNING LINK: FAILED (Status {response.status_code})")

if __name__ == "__main__":
    print("--- STARTING API TEST ---")
    test_root()
    test_create_signing_link_mock()
    print("--- END API TEST ---")
