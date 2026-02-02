from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import execution.workflow_proposals as wp
import execution.workflow_core as wc
import execution.workflow_signing as ws
import execution.seed_data as sd
import execution.pdf_generator as pdf

app = FastAPI(title="ProjexNest Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow Lovable/Internet to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class ClientCreate(BaseModel):
    org_id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None

class ProjectCreate(BaseModel):
    org_id: str
    client_id: str
    name: str
    status: str = "lead"

class TemplateCreate(BaseModel):
    org_id: str
    name: str
    content: Dict[str, Any]

class ProposalCreate(BaseModel):
    org_id: str
    project_id: str
    template_id: str
    title: str

class ProposalUpdate(BaseModel):
    proposal_id: str
    content: Dict[str, Any]
    user_id: str # mimicking auth user for version tracking

class SigningLinkCreate(BaseModel):
    proposal_version_id: str
    signer_email: Optional[str] = None
    expires_in_days: int = 7

class PublicSign(BaseModel):
    token: str
    signature_name: str
    signature_data: str # Base64 or string
    consent: bool = True

class OrganizationCreate(BaseModel):
    name: str
    user_id: str

# --- Core Routes ---

@app.get("/")
def read_root():
    return {"message": "ProjexNest Orchestrator Running. v1.1"}

@app.post("/workflow/organizations")
def create_organization(payload: OrganizationCreate):
    return wc.create_organization(payload.name, payload.user_id)

@app.post("/workflow/clients")
def create_client(payload: ClientCreate):
    return wc.create_client(payload.org_id, payload.name, payload.email, payload.phone, payload.address)

@app.get("/workflow/clients")
def list_clients(org_id: str):
    return wc.list_clients(org_id)

@app.post("/workflow/projects")
def create_project(payload: ProjectCreate):
    return wc.create_project(payload.org_id, payload.client_id, payload.name, payload.status)

@app.get("/workflow/projects")
def list_projects(org_id: str):
    return wc.list_projects(org_id)

@app.post("/workflow/projects/{project_id}/complete")
def complete_project(project_id: str):
    return wc.mark_project_complete(project_id)

# --- Proposal Routes ---

@app.get("/workflow/templates")
def list_templates(org_id: str):
    return wp.list_templates(org_id)

@app.post("/workflow/templates")
def create_template(payload: TemplateCreate):
    return wp.create_template(payload.org_id, payload.name, payload.content)

@app.get("/workflow/proposals")
def list_proposals(org_id: str):
    return wp.list_proposals(org_id)

@app.post("/workflow/proposals")
def create_proposal(payload: ProposalCreate):
    # Mapping 'title' to schema 'name' happens in execution layer
    return wp.create_proposal_from_template(
        payload.org_id, 
        payload.project_id, 
        payload.template_id, 
        payload.title
    )

@app.get("/workflow/proposals/{proposal_id}")
def get_proposal_detail(proposal_id: str):
    return wp.get_proposal_full(proposal_id)

@app.post("/workflow/proposals/draft")
def save_draft(payload: ProposalUpdate):
    return wp.update_proposal_content(payload.proposal_id, payload.content, payload.user_id)

@app.post("/workflow/signing-links")
def create_signing_link(payload: SigningLinkCreate):
    token = wp.generate_signing_link(
        payload.proposal_version_id, 
        payload.signer_email, 
        payload.expires_in_days
    )
    base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return {
        "token": token,
        "url": f"{base_url}/public/sign?token={token}"
    }

# --- PDF Generation ---

@app.get("/workflow/proposals/{proposal_id}/pdf")
def generate_proposal_pdf(proposal_id: str):
    """
    Generates and returns a PDF for the given proposal.
    """
    # 1. Get proposal details
    proposal_data = wp.get_proposal_full(proposal_id)
    if not proposal_data:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal = proposal_data.get("proposal", {})
    version = proposal_data.get("latest_version", {})
    content_json = version.get("content_json", {})
    
    # 2. Generate PDF
    try:
        pdf_bytes = pdf.generate_proposal_pdf(proposal, content_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    # 3. Return as downloadable file
    filename = f"proposal_{proposal_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- Public Signing Routes ---

@app.get("/public/proposals/{token}")
def get_public_proposal(token: str):
    data = ws.get_proposal_for_signing(token)
    if not data:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    return data

@app.post("/public/proposals/sign")
def sign_public_proposal(payload: PublicSign):
    success = ws.sign_proposal(
        payload.token, 
        payload.signature_name, 
        payload.signature_data, 
        consent=payload.consent
    )
    if not success:
        raise HTTPException(status_code=400, detail="Signing failed or link expired")
    return {"status": "signed"}

# --- Utility Routes ---
@app.post("/workflow/seed")
def trigger_seed():
    try:
        sd.seed()
        return {"status": "Seed completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

