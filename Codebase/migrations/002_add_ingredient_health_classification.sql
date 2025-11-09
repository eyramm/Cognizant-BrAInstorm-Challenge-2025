-- Migration: Add health classification to ingredients
-- Created: 2025-11-08
-- Description: Adds health classification fields to track harmful/safe ingredients

BEGIN;

-- Add health classification columns to ingredients table
ALTER TABLE ingredients
ADD COLUMN IF NOT EXISTS health_classification TEXT CHECK (health_classification IN ('good', 'caution', 'harmful')),
ADD COLUMN IF NOT EXISTS health_concerns TEXT,
ADD COLUMN IF NOT EXISTS is_additive BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS additive_code TEXT;

-- Create index for faster filtering by health classification
CREATE INDEX IF NOT EXISTS idx_ingredients_health_classification ON ingredients(health_classification);
CREATE INDEX IF NOT EXISTS idx_ingredients_is_additive ON ingredients(is_additive);
CREATE INDEX IF NOT EXISTS idx_ingredients_additive_code ON ingredients(additive_code) WHERE additive_code IS NOT NULL;

COMMIT;
