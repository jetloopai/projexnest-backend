-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ==============================================================================
-- 0. Core Logic & Enums (Idempotent)
-- ==============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        create type user_role as enum ('owner', 'admin', 'member');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status') THEN
        create type project_status as enum ('lead', 'active', 'completed', 'cancelled');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'proposal_status') THEN
        create type proposal_status as enum ('draft', 'sent', 'viewed', 'signed', 'declined', 'expired');
    END IF;
END$$;

-- ==============================================================================
-- 1. Core Tables (Organizations, Projects, Clients)
-- ==============================================================================

create table if not exists organizations (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  created_at timestamptz default now()
);

create table if not exists org_memberships (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organizations(id) not null,
  user_id uuid references auth.users(id) not null,
  role user_role default 'member',
  created_at timestamptz default now(),
  unique(org_id, user_id)
);

create table if not exists clients (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organizations(id) not null,
  name text not null,
  email text,
  phone text,
  address text,
  created_at timestamptz default now()
);

create table if not exists projects (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organizations(id) not null,
  client_id uuid references clients(id),
  name text not null,
  status project_status default 'lead',
  created_at timestamptz default now()
);

create table if not exists files (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organizations(id) not null,
  project_id uuid references projects(id), -- Optional
  name text not null,
  storage_path text not null,
  mime_type text,
  size_bytes bigint,
  created_at timestamptz default now()
);

create table if not exists proposals (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organizations(id) not null,
  project_id uuid references projects(id),
  title text not null,
  status proposal_status default 'draft',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ==============================================================================
-- 2. Proposal & Signing Tables
-- ==============================================================================

-- Proposal Templates
create table if not exists proposal_templates (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organizations(id) not null,
  name text not null,
  content_json jsonb not null default '{}'::jsonb,
  is_archived boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Proposal Versions
create table if not exists proposal_versions (
  id uuid primary key default uuid_generate_v4(),
  proposal_id uuid references proposals(id) not null,
  version_number int not null default 1,
  content_json jsonb not null,
  pdf_file_id uuid references files(id),
  created_at timestamptz default now(),
  created_by uuid references auth.users(id)
);

-- Signing Sessions (The link sent to a user)
create table if not exists signing_sessions (
  id uuid primary key default uuid_generate_v4(),
  proposal_version_id uuid references proposal_versions(id) not null,
  token text unique not null,
  status text not null default 'pending', -- pending, viewed, signed, declined, expired
  signer_email text, -- Optional, to track who this link was for
  viewer_ip text,
  viewer_user_agent text,
  opened_at timestamptz,
  signed_at timestamptz,
  expires_at timestamptz not null,
  created_at timestamptz default now()
);

-- Signatures (The actual capture)
create table if not exists signatures (
  id uuid primary key default uuid_generate_v4(),
  signing_session_id uuid references signing_sessions(id) not null,
  signer_name text not null,
  signature_type text, -- 'draw', 'type', 'upload'
  signature_data text, -- Data URL or text
  consent_agreed boolean not null default false,
  signed_at timestamptz default now(),
  ip_address text
);

-- ==============================================================================
-- 3. RLS Policies
-- ==============================================================================

-- Enable RLS
alter table organizations enable row level security;
alter table org_memberships enable row level security;
alter table clients enable row level security;
alter table projects enable row level security;
alter table files enable row level security;
alter table proposals enable row level security;
alter table proposal_templates enable row level security;
alter table proposal_versions enable row level security;
alter table signing_sessions enable row level security;
alter table signatures enable row level security;

-- Helper Function: is_org_member
create or replace function is_org_member(_org_id uuid)
returns boolean
language sql
security definer
as $$
  select exists (
    select 1
    from org_memberships
    where org_id = _org_id
    and user_id = auth.uid()
  );
$$;

-- Generic Org Member Policy logic
-- We apply these explicitly for clarity

-- Check if policies exist before creating (simple manual approach: Drop then Create is easiest for robust retry)
-- Or just create, if it errors "already exists" we might need DO block.
-- RLS policies usually ERROR if they exist.
-- Let's DROP IF EXISTS first to be safe.

drop policy if exists "Org members can view organizations" on organizations;
create policy "Org members can view organizations"
  on organizations for select
  using ( is_org_member(id) );

drop policy if exists "Users can view own memberships" on org_memberships;
create policy "Users can view own memberships"
  on org_memberships for select
  using ( user_id = auth.uid() );

drop policy if exists "Org members can view clients" on clients;
create policy "Org members can view clients"
  on clients for all
  using ( is_org_member(org_id) );

drop policy if exists "Org members can view projects" on projects;
create policy "Org members can view projects"
  on projects for all
  using ( is_org_member(org_id) );

drop policy if exists "Org members can view files" on files;
create policy "Org members can view files"
  on files for all
  using ( is_org_member(org_id) );

drop policy if exists "Org members can view proposals" on proposals;
create policy "Org members can view proposals"
  on proposals for all
  using ( is_org_member(org_id) );

drop policy if exists "Org members can manage templates" on proposal_templates;
create policy "Org members can manage templates"
  on proposal_templates for all
  using ( is_org_member(org_id) );

-- Version Access via Proposal
drop policy if exists "Org members can view versions" on proposal_versions;
create policy "Org members can view versions"
  on proposal_versions for select
  using (
    exists (
      select 1 from proposals
      where proposals.id = proposal_versions.proposal_id
      and is_org_member(proposals.org_id)
    )
  );

drop policy if exists "Org members can create versions" on proposal_versions;
create policy "Org members can create versions"
  on proposal_versions for insert
  with check (
    exists (
      select 1 from proposals
      where proposals.id = proposal_versions.proposal_id
      and is_org_member(proposals.org_id)
    )
  );

-- Signing Sessions RLS
drop policy if exists "Org members can view signing sessions" on signing_sessions;
create policy "Org members can view signing sessions"
  on signing_sessions for select
  using (
    exists (
      select 1 from proposal_versions
      join proposals on proposals.id = proposal_versions.proposal_id
      where proposal_versions.id = signing_sessions.proposal_version_id
      and is_org_member(proposals.org_id)
    )
  );

-- Signatures RLS
drop policy if exists "Org members can view signatures" on signatures;
create policy "Org members can view signatures"
  on signatures for select
  using (
    exists (
      select 1 from signing_sessions
      join proposal_versions on proposal_versions.id = signing_sessions.proposal_version_id
      join proposals on proposals.id = proposal_versions.proposal_id
      where signing_sessions.id = signatures.signing_session_id
      and is_org_member(proposals.org_id)
    )
  );

-- ==============================================================================
-- 4. Public RPC Functions
-- ==============================================================================

-- GET PROPOSAL FOR SIGNING (Security Definer to bypass RLS for token holding guests)
create or replace function get_proposal_for_signing(token_input text)
returns table (
  proposal_title text,
  content_json jsonb,
  status proposal_status,
  signer_email text
) 
language plpgsql
security definer
as $$
declare
  session_record signing_sessions%rowtype;
begin
  -- Find session
  select * into session_record
  from signing_sessions
  where token = token_input
  and expires_at > now();

  if not found then
    return; -- Returns empty
  end if;

  -- Update viewed status if pending
  if session_record.status = 'pending' then
    update signing_sessions
    set status = 'viewed', opened_at = now()
    where id = session_record.id;
  end if;

  -- Return data
  return query
  select 
    p.title as proposal_title,
    pv.content_json,
    session_record.status::proposal_status, -- cast text if needed, or if enum matches
    session_record.signer_email
  from proposal_versions pv
  join proposals p on p.id = pv.proposal_id
  where pv.id = session_record.proposal_version_id;
end;
$$;

-- SIGN PROPOSAL (Security Definer)
create or replace function sign_proposal_with_token(
  token_input text,
  signature_name_input text,
  consent_input boolean,
  signature_type_input text,
  signature_data_input text,
  user_agent_input text
)
returns boolean
language plpgsql
security definer
as $$
declare
  session_record signing_sessions%rowtype;
begin
  -- Validate
  select * into session_record
  from signing_sessions
  where token = token_input
  and status in ('pending', 'viewed') -- Can only sign if not already signed/expired
  and expires_at > now();

  if not found then
    return false;
  end if;

  -- Insert Signature
  insert into signatures (
    signing_session_id,
    signer_name,
    signature_type,
    signature_data,
    consent_agreed,
    ip_address
  ) values (
    session_record.id,
    signature_name_input,
    signature_type_input,
    signature_data_input,
    consent_input,
    'public_ip'
  );

  -- Update Session
  update signing_sessions
  set 
    status = 'signed',
    signed_at = now(),
    viewer_user_agent = user_agent_input
  where id = session_record.id;
  
  -- Update Proposal Status
  update proposals
  set status = 'signed'
  from proposal_versions pv
  where proposals.id = pv.proposal_id
  and pv.id = session_record.proposal_version_id;

  return true;
end;
$$;
