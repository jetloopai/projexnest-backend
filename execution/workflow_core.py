from typing import Dict, Any, List, Optional
from execution.supabase_client import get_client

supabase = get_client()

# --- Clients ---
def create_organization(name: str, user_id: str) -> Dict[str, Any]:
    # 1. Create Org
    org_resp = supabase.table("organizations").insert({"name": name}).execute()
    org_id = org_resp.data[0]["id"]
    
    # 2. Add User as Owner
    member_data = {
        "org_id": org_id,
        "user_id": user_id,
        "role": "owner"
    }
    supabase.table("org_memberships").insert(member_data).execute()
    
    return org_resp.data[0]

def create_client(org_id: str, name: str, email: str, phone: str = None, address: str = None) -> Dict[str, Any]:
    data = {
        "org_id": org_id,
        "name": name,
        "email": email,
        "phone": phone,
        "address": address
    }
    response = supabase.table("clients").insert(data).execute()
    return response.data[0]

def update_client(client_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    response = supabase.table("clients").update(updates).eq("id", client_id).execute()
    return response.data[0] if response.data else None

def list_clients(org_id: str) -> List[Dict[str, Any]]:
    response = supabase.table("clients").select("*").eq("org_id", org_id).execute()
    return response.data

# --- Projects ---
def create_project(org_id: str, client_id: str, name: str, status: str = "lead") -> Dict[str, Any]:
    data = {
        "org_id": org_id,
        "client_id": client_id,
        "name": name,
        "status": status
    }
    response = supabase.table("projects").insert(data).execute()
    return response.data[0]

def update_project(project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    response = supabase.table("projects").update(updates).eq("id", project_id).execute()
    return response.data[0] if response.data else None

def mark_project_complete(project_id: str) -> Dict[str, Any]:
    return update_project(project_id, {"status": "completed"})

def list_projects(org_id: str) -> List[Dict[str, Any]]:
    response = supabase.table("projects").select("*, clients(name)").eq("org_id", org_id).execute()
    return response.data
