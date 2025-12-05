-- Migration: Add summary field to documents table
-- Created: 2024-12-05
-- Description: Add AI-generated summary field for better document preview

-- Add summary column to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS summary TEXT;

-- Add comment to summary column
COMMENT ON COLUMN documents.summary IS 'AI-generated document summary';

-- Create index for summary search (optional, for future full-text search)
-- CREATE INDEX IF NOT EXISTS idx_documents_summary ON documents USING gin(to_tsvector('english', summary));
