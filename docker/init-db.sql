-- Database initialization script for 9P Social Analytics
-- This script creates the initial database schema and indexes

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create brands table
CREATE TABLE IF NOT EXISTS brands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    industry VARCHAR(100),
    website_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create social_posts table
CREATE TABLE IF NOT EXISTS social_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    platform_post_id VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    author_username VARCHAR(255),
    author_display_name VARCHAR(255),
    posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    engagement_likes INTEGER DEFAULT 0,
    engagement_shares INTEGER DEFAULT 0,
    engagement_comments INTEGER DEFAULT 0,
    engagement_views INTEGER DEFAULT 0,
    raw_data JSONB,
    s3_raw_key VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, platform_post_id)
);

-- Create classifications table
CREATE TABLE IF NOT EXISTS classifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES social_posts(id) ON DELETE CASCADE,
    nine_p_product DECIMAL(4,3) DEFAULT 0.0,
    nine_p_place DECIMAL(4,3) DEFAULT 0.0,
    nine_p_price DECIMAL(4,3) DEFAULT 0.0,
    nine_p_publicity DECIMAL(4,3) DEFAULT 0.0,
    nine_p_postconsumption DECIMAL(4,3) DEFAULT 0.0,
    nine_p_purpose DECIMAL(4,3) DEFAULT 0.0,
    nine_p_partnerships DECIMAL(4,3) DEFAULT 0.0,
    nine_p_people DECIMAL(4,3) DEFAULT 0.0,
    nine_p_planet DECIMAL(4,3) DEFAULT 0.0,
    sentiment_label VARCHAR(20) NOT NULL,
    sentiment_positive DECIMAL(4,3) DEFAULT 0.0,
    sentiment_neutral DECIMAL(4,3) DEFAULT 0.0,
    sentiment_negative DECIMAL(4,3) DEFAULT 0.0,
    confidence_score DECIMAL(4,3) DEFAULT 0.0,
    classification_method VARCHAR(50) NOT NULL,
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id)
);

-- Create monthly_aggregates table
CREATE TABLE IF NOT EXISTS monthly_aggregates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_posts INTEGER DEFAULT 0,
    avg_nine_p_product DECIMAL(4,3) DEFAULT 0.0,
    avg_nine_p_place DECIMAL(4,3) DEFAULT 0.0,
    avg_nine_p_price DECIMAL(4,3) DEFAULT 0.0,
    avg_nine_p_publicity DECIMAL(4,3) DEFAULT 0.0,
    avg_nine_p_postconsumption DECIMAL(4,3) DEFAULT 0.0,
    avg_nine_p_purpose DECIMAL(4,3) DEFAULT 0.0,
    avg_nine_p_partnerships DECIMAL(4,3) DEFAULT 0.0,
    avg_nine_p_people DECIMAL(4,3) DEFAULT 0.0,
    avg_nine_p_planet DECIMAL(4,3) DEFAULT 0.0,
    sentiment_positive_count INTEGER DEFAULT 0,
    sentiment_neutral_count INTEGER DEFAULT 0,
    sentiment_negative_count INTEGER DEFAULT 0,
    avg_sentiment_positive DECIMAL(4,3) DEFAULT 0.0,
    avg_sentiment_neutral DECIMAL(4,3) DEFAULT 0.0,
    avg_sentiment_negative DECIMAL(4,3) DEFAULT 0.0,
    total_engagement_likes BIGINT DEFAULT 0,
    total_engagement_shares BIGINT DEFAULT 0,
    total_engagement_comments BIGINT DEFAULT 0,
    total_engagement_views BIGINT DEFAULT 0,
    avg_engagement_likes DECIMAL(8,2) DEFAULT 0.0,
    avg_engagement_shares DECIMAL(8,2) DEFAULT 0.0,
    avg_engagement_comments DECIMAL(8,2) DEFAULT 0.0,
    avg_engagement_views DECIMAL(8,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(brand_id, platform, year, month)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_social_posts_brand_id ON social_posts(brand_id);
CREATE INDEX IF NOT EXISTS idx_social_posts_platform ON social_posts(platform);
CREATE INDEX IF NOT EXISTS idx_social_posts_posted_at ON social_posts(posted_at);
CREATE INDEX IF NOT EXISTS idx_social_posts_platform_post_id ON social_posts(platform_post_id);
CREATE INDEX IF NOT EXISTS idx_social_posts_text_gin ON social_posts USING gin(text gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_classifications_post_id ON classifications(post_id);
CREATE INDEX IF NOT EXISTS idx_classifications_sentiment_label ON classifications(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_classifications_confidence_score ON classifications(confidence_score);
CREATE INDEX IF NOT EXISTS idx_classifications_method ON classifications(classification_method);

CREATE INDEX IF NOT EXISTS idx_monthly_aggregates_brand_platform ON monthly_aggregates(brand_id, platform);
CREATE INDEX IF NOT EXISTS idx_monthly_aggregates_year_month ON monthly_aggregates(year, month);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_social_posts_brand_platform_date ON social_posts(brand_id, platform, posted_at);
CREATE INDEX IF NOT EXISTS idx_classifications_sentiment_confidence ON classifications(sentiment_label, confidence_score);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_social_posts_updated_at BEFORE UPDATE ON social_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_classifications_updated_at BEFORE UPDATE ON classifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_monthly_aggregates_updated_at BEFORE UPDATE ON monthly_aggregates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample brands for testing
INSERT INTO brands (name, description, industry, website_url) VALUES
    ('TechCorp', 'Leading technology company', 'Technology', 'https://techcorp.com'),
    ('FashionBrand', 'Premium fashion retailer', 'Fashion', 'https://fashionbrand.com'),
    ('FoodChain', 'Global restaurant chain', 'Food & Beverage', 'https://foodchain.com')
ON CONFLICT (name) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW post_classifications AS
SELECT 
    sp.id,
    sp.brand_id,
    b.name as brand_name,
    sp.platform,
    sp.text,
    sp.posted_at,
    sp.engagement_likes,
    sp.engagement_shares,
    sp.engagement_comments,
    c.nine_p_product,
    c.nine_p_place,
    c.nine_p_price,
    c.nine_p_publicity,
    c.nine_p_postconsumption,
    c.nine_p_purpose,
    c.nine_p_partnerships,
    c.nine_p_people,
    c.nine_p_planet,
    c.sentiment_label,
    c.sentiment_positive,
    c.sentiment_neutral,
    c.sentiment_negative,
    c.confidence_score,
    c.classification_method
FROM social_posts sp
JOIN brands b ON sp.brand_id = b.id
LEFT JOIN classifications c ON sp.id = c.post_id;

-- Create materialized view for dashboard metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_metrics AS
SELECT 
    b.id as brand_id,
    b.name as brand_name,
    sp.platform,
    DATE_TRUNC('day', sp.posted_at) as date,
    COUNT(*) as post_count,
    AVG(c.nine_p_product) as avg_product,
    AVG(c.nine_p_place) as avg_place,
    AVG(c.nine_p_price) as avg_price,
    AVG(c.nine_p_publicity) as avg_publicity,
    AVG(c.nine_p_postconsumption) as avg_postconsumption,
    AVG(c.nine_p_purpose) as avg_purpose,
    AVG(c.nine_p_partnerships) as avg_partnerships,
    AVG(c.nine_p_people) as avg_people,
    AVG(c.nine_p_planet) as avg_planet,
    COUNT(CASE WHEN c.sentiment_label = 'positive' THEN 1 END) as positive_count,
    COUNT(CASE WHEN c.sentiment_label = 'neutral' THEN 1 END) as neutral_count,
    COUNT(CASE WHEN c.sentiment_label = 'negative' THEN 1 END) as negative_count,
    AVG(sp.engagement_likes + sp.engagement_shares + sp.engagement_comments) as avg_engagement
FROM brands b
JOIN social_posts sp ON b.id = sp.brand_id
LEFT JOIN classifications c ON sp.id = c.post_id
GROUP BY b.id, b.name, sp.platform, DATE_TRUNC('day', sp.posted_at);

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_dashboard_metrics_brand_platform_date 
ON dashboard_metrics(brand_id, platform, date);

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_dashboard_metrics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_metrics;
END;
$$ LANGUAGE plpgsql;
