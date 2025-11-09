-- Migration: Add image columns to products table
-- Created: 2025-11-08
-- Description: Adds image_url and image_small_url columns to store product images

BEGIN;

-- Add image columns if they don't exist
ALTER TABLE products
ADD COLUMN IF NOT EXISTS image_url TEXT,
ADD COLUMN IF NOT EXISTS image_small_url TEXT;

-- Migrate existing data from raw_off_data JSONB to new columns
UPDATE products
SET
  image_url = raw_off_data->>'image_front_url',
  image_small_url = raw_off_data->>'image_front_small_url'
WHERE image_url IS NULL
  AND raw_off_data IS NOT NULL;

-- Create indexes for faster image lookups (optional, only if needed)
-- CREATE INDEX IF NOT EXISTS idx_products_image_url ON products(image_url) WHERE image_url IS NOT NULL;

COMMIT;
