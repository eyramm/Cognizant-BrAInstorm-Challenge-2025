-- Migration: Add product_summaries table for AI-generated summaries
-- Created: 2025-11-08
-- Description: Cache AI-generated product summaries to reduce API calls and costs

BEGIN;

-- Create table for storing AI-generated product summaries
CREATE TABLE IF NOT EXISTS product_summaries (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT UNIQUE NOT NULL REFERENCES products(id) ON DELETE CASCADE,

    -- AI-generated summary text
    summary TEXT NOT NULL,

    -- Model information
    ai_model VARCHAR(50) DEFAULT 'gemini-1.5-flash',

    -- Summary metadata
    summary_version INTEGER DEFAULT 1,  -- Increment when regenerating

    -- Timestamps
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_product_summaries_product ON product_summaries(product_id);
CREATE INDEX IF NOT EXISTS idx_product_summaries_generated ON product_summaries(generated_at DESC);

-- Update trigger
CREATE OR REPLACE FUNCTION update_summary_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_product_summaries_updated_at ON product_summaries;
CREATE TRIGGER update_product_summaries_updated_at
    BEFORE UPDATE ON product_summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_summary_updated_at();

COMMIT;
