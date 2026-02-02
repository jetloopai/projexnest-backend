import uuid
from typing import Dict, Any, List
from execution.supabase_client import get_client

supabase = get_client()

def create_template(org_id: str, name: str, content: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new proposal template."""
    data = {
        "org_id": org_id,
        "name": name,
        "content_json": content,
        "template_type": "client_proposal" # Default for legacy schema compatibility
    }
    response = supabase.table("proposal_templates").insert(data).execute()
    return response.data[0]

def create_proposal_from_template(org_id: str, project_id: str, template_id: str, title: str) -> Dict[str, Any]:
    """Creates a proposal from a template."""
    
    # 1. Fetch Template
    tmpl_resp = supabase.table("proposal_templates").select("*").eq("id", template_id).single().execute()
    template = tmpl_resp.data
    
    # 2. Create Proposal
    prop_data = {
        "org_id": org_id,
        "project_id": project_id,
        "name": title, # Schema uses 'name' not 'title'
        "status": "draft"
    }
    prop_resp = supabase.table("proposals").insert(prop_data).execute()
    proposal = prop_resp.data[0]
    
    # 3. Create First Version
    ver_data = {
        "org_id": org_id, # Required by legacy schema
        "proposal_id": proposal["id"],
        "version_number": 1,
        "content_json": template["content_json"],
        "created_by": "938d1d2f-bbcd-4c0e-b202-3d5ede2a166c" # Valid User ID
    }
    ver_resp = supabase.table("proposal_versions").insert(ver_data).execute()
    
    return {
        "proposal": proposal,
        "version": ver_resp.data[0]
    }

def generate_signing_link(proposal_version_id: str, signer_email: str = None, expires_in_days: int = 7) -> str:
    """Generates a signing link (session) for a proposal version."""
    import datetime
    
    token = str(uuid.uuid4())
    expires_at = datetime.datetime.now() + datetime.timedelta(days=expires_in_days)
    
    data = {
        "proposal_version_id": proposal_version_id,
        "token": token,
        "status": "pending",
        "signer_email": signer_email,
        "expires_at": expires_at.isoformat()
    }
    
    supabase.table("signing_sessions").insert(data).execute()
    
    # Return details
    # We might want to construct the URL here if we had the base URL
    return token

def list_templates(org_id: str) -> List[Dict[str, Any]]:
    response = supabase.table("proposal_templates").select("*").eq("org_id", org_id).execute()
    return response.data

def list_proposals(org_id: str) -> List[Dict[str, Any]]:
    response = supabase.table("proposals").select("*, clients(name), projects(name)").eq("org_id", org_id).execute()
    return response.data

def get_proposal_full(proposal_id: str) -> Dict[str, Any]:
    """
    Fetches complete proposal data including:
    - Proposal details (scope_of_work, total, etc.)
    - Related client and project names
    - Latest version for version-specific data
    """
    # Get proposal with related data
    p_resp = supabase.table("proposals").select(
        "*, clients(id, name, email), projects(id, name)"
    ).eq("id", proposal_id).single().execute()
    
    # Get versions
    v_resp = supabase.table("proposal_versions").select("*").eq(
        "proposal_id", proposal_id
    ).order("version_number", desc=True).execute()
    
    if not p_resp.data:
        return None
    
    proposal = p_resp.data
    versions = v_resp.data if v_resp.data else []
    latest_version = versions[0] if versions else {}
    
    return {
        "proposal": proposal,
        "client": proposal.get("clients"),
        "project": proposal.get("projects"),
        "versions": versions,
        "latest_version": latest_version
    }

def update_proposal_content(proposal_id: str, content: Dict[str, Any], created_by: str) -> Dict[str, Any]:
    """
    Saves a new draft version of the proposal.
    """
    # Get current latest version number
    curr_ver = supabase.table("proposal_versions").select("version_number, org_id").eq("proposal_id", proposal_id).order("version_number", desc=True).limit(1).execute()
    
    next_num = 1
    org_id = None
    if curr_ver.data:
        next_num = curr_ver.data[0]["version_number"] + 1
        org_id = curr_ver.data[0]["org_id"]
    else:
        # Fallback if no version exists (shouldn't happen if created correctly)
        prop = supabase.table("proposals").select("org_id").eq("id", proposal_id).single().execute()
        org_id = prop.data["org_id"]

    data = {
        "proposal_id": proposal_id,
        "org_id": org_id,
        "version_number": next_num,
        "content_json": content,
        "created_by": created_by
    }
    
    response = supabase.table("proposal_versions").insert(data).execute()
    
    # Update proposal updated_at
    supabase.table("proposals").update({"updated_at": "now()"}).eq("id", proposal_id).execute()
    
    return response.data[0]

def get_proposal_details(proposal_id: str) -> Dict[str, Any]:
    """Fetches full proposal details including latest version."""
    return get_proposal_full(proposal_id)
