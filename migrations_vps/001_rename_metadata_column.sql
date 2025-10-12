-- Migration: Rename 'metadata' column to 'article_metadata' in articles table
-- Reason: 'metadata' is reserved by SQLAlchemy MetaData class
-- Run this BEFORE importing user data on VPS

-- Check if articles table exists and has 'metadata' column
-- If it does, rename it to 'article_metadata'

USE ezwai_smm_db;

-- Add new column if it doesn't exist
ALTER TABLE articles ADD COLUMN IF NOT EXISTS article_metadata JSON COMMENT 'Article metadata (renamed from metadata to avoid SQLAlchemy conflict)';

-- Copy data from old column if it exists
UPDATE articles SET article_metadata = metadata WHERE metadata IS NOT NULL AND article_metadata IS NULL;

-- Drop old column if it exists
ALTER TABLE articles DROP COLUMN IF EXISTS metadata;

-- Verify migration
SELECT 'Migration complete: metadata → article_metadata' AS status;
