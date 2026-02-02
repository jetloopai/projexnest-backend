from typing import Dict, Any, Optional
from execution.supabase_client import get_client

supabase = get_client()

def get_proposal_for_signing(token: str) -> Optional[Dict[str, Any]]:
    """
    Calls the Security Definer RPC to safely retrieve proposal details 
    for a public user holding a valid token.
    """
    try:
        # Call the RPC function defined in schema.sql
        response = supabase.rpc("get_proposal_for_signing", {"token_input": token}).execute()
        
        # RPC returns a list of rows, we expect one or none
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching proposal for signing: {e}")
        return None

def sign_proposal(token: str, signature_name: str, signature_data: str, user_agent: str = "Script/1.0", consent: bool = True) -> bool:
    """
    Calls the Security Definer RPC to sign the proposal.
    """
    try:
        payload = {
            "token_input": token,
            "signature_name_input": signature_name,
            "consent_input": consent,
            "signature_type_input": "text", # Defaulting to text for script simplicity
            "signature_data_input": signature_data,
            "user_agent_input": user_agent
        }
        
        response = supabase.rpc("sign_proposal_with_token", payload).execute()
        return response.data # Returns boolean from valid PLPGSQL function
    except Exception as e:
        print(f"Error signing proposal: {e}")
        return False
