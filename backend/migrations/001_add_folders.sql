-- Migration: Add folders table and update documents table
-- Created: 2025-11-24
-- Description: Add folder functionality to organize documents

-- Create folders table
CREATE TABLE IF NOT EXISTS folders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    parent_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
    path VARCHAR(1000) NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for folders table
CREATE INDEX IF NOT EXISTS idx_folders_owner_id ON folders(owner_id);
CREATE INDEX IF NOT EXISTS idx_folders_parent_id ON folders(parent_id);
CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path);

-- Add folder_id column to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL;

-- Create index for folder_id in documents table
CREATE INDEX IF NOT EXISTS idx_documents_folder_id ON documents(folder_id);

-- Add comment to folder_id column
COMMENT ON COLUMN documents.folder_id IS 'Folder ID (NULL for root level)';
