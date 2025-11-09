-- Migration: Add cached transportation data to products table
-- Created: 2025-11-08
-- Description: Pre-calculate transportation scores to avoid geocoding on every request

BEGIN;

-- Add columns for cached transportation data
ALTER TABLE products
ADD COLUMN IF NOT EXISTS manufacturing_distance_km DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS manufacturing_lat DECIMAL(10,7),
ADD COLUMN IF NOT EXISTS manufacturing_lon DECIMAL(10,7),
ADD COLUMN IF NOT EXISTS transportation_co2_kg DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS transportation_score INTEGER;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_products_transportation_score ON products(transportation_score);

COMMIT;
