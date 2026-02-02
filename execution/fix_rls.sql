-- Drop duplicate and recursive policies
DROP POLICY IF EXISTS "Org owners manage memberships" ON org_memberships;
DROP POLICY IF EXISTS "org_memberships_owner_manage" ON org_memberships;
DROP POLICY IF EXISTS "org_memberships_read_own" ON org_memberships;
DROP POLICY IF EXISTS "Users can view own memberships" ON org_memberships; -- Re-applying this one correctly too

-- Ensure we keep the basic read policy
CREATE POLICY "Users can view own memberships"
  ON org_memberships FOR SELECT
  USING ( user_id = auth.uid() );

-- Create helper function that bypasses RLS
CREATE OR REPLACE FUNCTION public.is_org_owner(p_org_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM org_memberships
    WHERE org_id = p_org_id
      AND user_id = auth.uid()
      AND role = 'user_role_owner'::text -- Casting to text to match logic or enum if needed. 
      -- Wait, schema uses enum 'owner'.
  );
$$;

-- Fix Function to match ENUM
CREATE OR REPLACE FUNCTION public.is_org_owner(p_org_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM org_memberships
    WHERE org_id = p_org_id
      AND user_id = auth.uid()
      AND role = 'owner'
  );
$$;

-- Allow owners to manage memberships (INSERT, UPDATE, DELETE)
-- First drop just in case
DROP POLICY IF EXISTS "Owners can manage org memberships" ON org_memberships;

CREATE POLICY "Owners can manage org memberships"
  ON org_memberships
  FOR ALL
  USING (public.is_org_owner(org_id))
  WITH CHECK (public.is_org_owner(org_id));
