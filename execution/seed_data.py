import random
import uuid
from execution.supabase_client import get_client
from execution.workflow_proposals import create_template, create_proposal_from_template, generate_signing_link
import time

supabase = get_client()

def seed():
    print("--- STARTING SEED ---")
    
    # 1. Create Organization (We need one owner user, but for script we might mimic one or just insert)
    # Since we can't easily create auth users via client API without admin rights, 
    # we will assumme we can insert into 'organizations' directly.
    
    org_id = str(uuid.uuid4())
    print(f"Creating Org: {org_id}")
    supabase.table("organizations").insert({"id": org_id, "name": "Demo Construction Co."}).execute()
    
    # 2. Create Clients
    clients = []
    for i in range(5):
        c = {
            "org_id": org_id,
            "name": f"Client {i+1} Homeowner",
            "email": f"client{i+1}@example.com"
        }
        res = supabase.table("clients").insert(c).execute()
        clients.append(res.data[0])
    print(f"Created {len(clients)} clients")
    
    # 3. Create Projects
    projects = []
    for c in clients:
        p = {
            "org_id": org_id,
            "client_id": c["id"],
            "name": f"{c['name']}'s Renovation",
            "status": random.choice(["lead", "active", "completed"])
        }
        res = supabase.table("projects").insert(p).execute()
        projects.append(res.data[0])
    print(f"Created {len(projects)} projects")
    
    # 4. Create Template
    tmpl = create_template(org_id, "Standard Bathroom Remodel", {
        "sections": [
            {"title": "Scope", "content": "Full demo and rebuild."},
            {"title": "Payment", "content": "50% down, 50% completion."}
        ]
    })
    print(f"Created Template: {tmpl['id']}")
    
    # 5. Create Proposals & Links
    for p in projects[:2]: # First 2 projects get proposals
        print(f"Generating proposal for {p['name']}...")
        result = create_proposal_from_template(org_id, p['id'], tmpl['id'], f"Proposal for {p['name']}")
        prop = result['proposal']
        ver = result['version']
        
        # Determine status
        if random.random() > 0.5:
             # Generate link
             token = generate_signing_link(ver['id'], "client@example.com")
             print(f" -> Generated Signing Link: /public/proposals/view?token={token}")
             
             # Optionally update status to 'sent'
             supabase.table("proposals").update({"status": "sent"}).eq("id", prop['id']).execute()
        
    print("--- SEED COMPLETE ---")

import logging

# Configure logging to file
logging.basicConfig(filename='seed_log.txt', level=logging.INFO, format='%(asctime)s %(message)s')

def print(msg):
    logging.info(msg)
    # Also print to stdout just in case
    import builtins
    builtins.print(msg)

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        logging.error("SEED FAILED", exc_info=True)
        # Re-raise to simple print
        import builtins
        builtins.print(f"FAILED: {e}")
        if hasattr(e, 'message'):
             builtins.print(f"Message: {e.message}")
        if hasattr(e, 'response'): 
             try:
                 builtins.print(e.response.text()) 
             except: pass
        exit(1)
