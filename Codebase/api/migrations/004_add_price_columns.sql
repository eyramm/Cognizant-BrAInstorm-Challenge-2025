-- Migration: Add price columns to products table
-- Created: 2025-11-08
-- Description: Add USD price and price_updated_at columns to support price display in recommendations

BEGIN;

-- Add columns for price data
ALTER TABLE products
ADD COLUMN IF NOT EXISTS price DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS price_updated_at TIMESTAMPTZ;

-- Create index for faster price queries
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price) WHERE price IS NOT NULL;

COMMIT;
