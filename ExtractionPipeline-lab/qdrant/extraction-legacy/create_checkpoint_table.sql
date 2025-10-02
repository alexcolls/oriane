-- Create the extraction_checkpoint table
-- This table stores the last processed ID for resuming extraction after interruption

CREATE TABLE IF NOT EXISTS public.extraction_checkpoint (
    id BIGINT PRIMARY KEY,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on updated_at for potential future queries
CREATE INDEX IF NOT EXISTS idx_extraction_checkpoint_updated_at
ON public.extraction_checkpoint (updated_at);

-- Add a comment to document the table's purpose
COMMENT ON TABLE public.extraction_checkpoint IS 'Stores the last processed ID for the extraction pipeline to enable resuming after interruption';
COMMENT ON COLUMN public.extraction_checkpoint.id IS 'The ID of the last successfully processed insta_content record';
COMMENT ON COLUMN public.extraction_checkpoint.updated_at IS 'Timestamp when the checkpoint was last updated';
