# ProjexNest — Antigravity Build Prompt (Backend + Automations)

## Goal
Implement the backend automation + API for **ProjexNest** using:
- **Supabase Postgres** (data)
- **Supabase Auth** (identity)
- **Supabase Storage** (files)
- Antigravity exposes workflow endpoints and public signing endpoints

**Non-negotiables**
- No Make.com
- No GoHighLevel
- Multi-tenant isolation (org_id everywhere)
- RLS enabled on all tables
- All workflows:
  1) Validate input
  2) Auth + org checks
  3) DB write(s)
  4) Log event
  5) Return structured JSON

---

## Data Model (Supabase)
Core tables already exist:
- organizations, org_memberships
- clients, projects, quotes, proposals
- subcontractors, project_subcontractors, subcontractor_payments
- materials, files, events

Proposal builder tables to add:
- proposal_templates
- proposal_versions
- proposal_recipients
- signing_sessions
- signatures

---

## Security Model
- RLS on all tables
- Membership-based access via `org_memberships`
- Helper functions:
  - `is_org_member(org_id)`
  - `has_org_role(org_id, roles[])`
- Public signing access is via **token-based security definer RPC**, not RLS bypass.

---

## Required Endpoints

### Core CRUD / workflows (examples)
- `POST /workflow/create_client`
- `POST /workflow/update_client`
- `POST /workflow/create_project`
- `POST /workflow/update_project`
- `POST /workflow/mark_project_complete`
- `POST /workflow/create_quote`
- `POST /workflow/send_quote`
- `POST /workflow/accept_quote`

### Proposal Builder
- `POST /workflow/templates/create`
- `POST /workflow/templates/update`
- `GET /views/templates/list`

- `POST /workflow/proposals/create_from_template`
- `POST /workflow/proposals/save_draft`
- `POST /workflow/proposals/generate_pdf_preview`
- `POST /workflow/proposals/send`
- `POST /workflow/proposals/mark_declined`
- `POST /workflow/proposals/expire`
- `GET /views/proposals/list`
- `GET /views/proposals/detail?id=...`

### Public Signing (no login)
- `GET /public/proposals/view?token=...`
  - returns proposal details + signed URL to PDF preview
- `POST /public/proposals/sign`
  - validates token, captures signature, locks proposal, stores signed PDF, logs events

Implementation recommended:
- Use Supabase RPC functions:
  - `public.get_proposal_for_signing(token text)`
  - `public.sign_proposal_with_token(token text, signature_name text, consent boolean, signature_type text, signature_data text, user_agent text)`

---

## PDF Generation
Antigravity must generate PDFs server-side:
1. Convert proposal `content_json` → HTML
2. Render HTML → PDF
3. Store to Supabase Storage bucket `projexnest`
4. Create row in `public.files`
5. Link file to `proposal_versions.pdf_file_id`
6. On signature, generate a final “SIGNED” PDF version and store its sha256 hash

Storage path pattern:
`org/{org_id}/projects/{project_id}/proposals/{proposal_id}/v{n}.pdf`

---

## Event Logging
Insert into `public.events` for every significant action:
- proposal_created
- proposal_sent
- proposal_viewed (optional)
- proposal_signed
- quote_sent
- project_completed
etc.

---

## Notifications (Optional Module)
If customer enables comms:
- SMS: Twilio or Telnyx (adapter layer)
- Email: SendGrid or SES
Triggers:
- Quote follow-ups
- Proposal reminders
- Review requests
- Warranty reminders
This module is optional and must not block core project tracking.

---

## Demo Data Seeding
Workflow: `POST /workflow/seed_demo_data`
Must generate:
- 5 clients
- 4 quotes (mixed statuses)
- 2 proposals (1 signed)
- 4 projects (3 active, 1 completed)
- 3 subcontractors + assignments
- 10 materials
- 8 files metadata
- 25 events
Ensure dashboard stats return non-zero values.

---

## Output Required
- Supabase schema + RLS policies applied
- Public signing RPC functions implemented
- Endpoint request/response examples
- Test plan for:
  - proposal builder save/version
  - send link creation
  - token validation
  - signing + lock behavior
  - PDF generation
