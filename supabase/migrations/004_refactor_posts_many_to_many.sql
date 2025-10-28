-- Migration: Refactor posts to support many-to-many relationship with analyses
-- This allows posts to be reused across multiple analyses, saving classification costs

-- Step 1: Create the junction table
CREATE TABLE IF NOT EXISTS analysis_posts (
  analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (analysis_id, post_id)
);

-- Step 2: Migrate existing data from posts.analysis_id to junction table
-- Only run this if you have existing data
INSERT INTO analysis_posts (analysis_id, post_id, created_at)
SELECT analysis_id, id, created_at
FROM posts
WHERE analysis_id IS NOT NULL
ON CONFLICT (analysis_id, post_id) DO NOTHING;

-- Step 3: Remove the analysis_id foreign key constraint from posts table
ALTER TABLE posts DROP CONSTRAINT IF EXISTS posts_analysis_id_fkey;
ALTER TABLE posts DROP COLUMN IF EXISTS analysis_id;

-- Step 4: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_analysis_posts_analysis ON analysis_posts(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analysis_posts_post ON analysis_posts(post_id);

-- Step 5: Drop old index
DROP INDEX IF EXISTS idx_posts_analysis;

-- Step 6: Enable RLS on new table
ALTER TABLE analysis_posts ENABLE ROW LEVEL SECURITY;

-- Step 7: Create RLS policy (adjust based on your auth setup)
CREATE POLICY "Enable all access for analysis_posts" ON analysis_posts
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Verify the migration
-- SELECT COUNT(*) FROM posts;
-- SELECT COUNT(*) FROM analysis_posts;
-- SELECT COUNT(*) FROM classifications;
