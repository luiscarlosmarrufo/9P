-- analyses table: stores each brand analysis job
CREATE TABLE analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_name TEXT NOT NULL,
  date_range TEXT NOT NULL, -- '7days', '30days', '90days'
  start_date TIMESTAMPTZ NOT NULL,
  end_date TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
  total_posts INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- posts table: stores unique social media posts (shared across analyses)
CREATE TABLE posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL, -- 'reddit' or 'twitter'
  post_id TEXT NOT NULL, -- original ID from Reddit/Twitter
  text TEXT NOT NULL,
  author TEXT,
  url TEXT,
  engagement INTEGER DEFAULT 0, -- upvotes/likes
  timestamp TIMESTAMPTZ,
  subreddit TEXT, -- nullable, only for Reddit
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(post_id, source) -- prevent duplicates
);

-- analysis_posts: junction table for many-to-many relationship
CREATE TABLE analysis_posts (
  analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (analysis_id, post_id)
);

-- classifications table: stores ML classifications for each post
CREATE TABLE classifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  categories JSONB NOT NULL, -- array of 9Ps categories
  sentiment TEXT NOT NULL, -- 'positive', 'neutral', 'negative'
  confidence FLOAT,
  reasoning TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(post_id) -- one classification per post
);

-- insights table: stores AI-generated strategic insights
CREATE TABLE insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  executive_summary TEXT NOT NULL,
  key_findings JSONB NOT NULL,
  recommendations JSONB NOT NULL,
  opportunities JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(analysis_id) -- one set of insights per analysis
);

-- Indexes for performance
CREATE INDEX idx_analyses_brand ON analyses(brand_name);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_posts_source ON posts(source);
CREATE INDEX idx_posts_timestamp ON posts(timestamp);
CREATE INDEX idx_analysis_posts_analysis ON analysis_posts(analysis_id);
CREATE INDEX idx_analysis_posts_post ON analysis_posts(post_id);
CREATE INDEX idx_classifications_post ON classifications(post_id);
CREATE INDEX idx_insights_analysis ON insights(analysis_id);
