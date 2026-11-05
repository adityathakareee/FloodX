-- FLOOD-X Database Initialization
-- Phase 0: Ensure PostGIS spatial extensions are enabled
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verification comment
COMMENT ON EXTENSION postgis IS 'PostGIS spatial and geographic objects and functions for FLOOD-X Pune basin models';

