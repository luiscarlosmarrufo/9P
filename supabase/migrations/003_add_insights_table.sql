-- Migration: Add insights table for strategic recommendations
-- Run this in your Supabase SQL Editor if the insights table doesn't exist

-- Drop existing table if you need to recreate it (CAREFUL: this deletes all data)
-- DROP TABLE IF EXISTS insights CASCADE;

-- Create insights table
CREATE TABLE IF NOT EXISTS insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  executive_summary TEXT NOT NULL,
  key_findings JSONB NOT NULL,
  recommendations JSONB NOT NULL,
  opportunities JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(analysis_id)
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_insights_analysis ON insights(analysis_id);

-- Enable Row Level Security (RLS)
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (adjust based on your auth setup)
-- For now, allow all operations (you should restrict this in production)
CREATE POLICY "Enable all access for insights" ON insights
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Grant permissions to authenticated users (if using Supabase Auth)
-- GRANT ALL ON insights TO authenticated;
-- GRANT ALL ON insights TO anon;
