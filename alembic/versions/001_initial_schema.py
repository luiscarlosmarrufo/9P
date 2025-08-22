"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    
    # Create brands table
    op.create_table('brands',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create social_posts table
    op.create_table('social_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('platform_post_id', sa.String(length=255), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('author_username', sa.String(length=255), nullable=True),
        sa.Column('author_display_name', sa.String(length=255), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('engagement_likes', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('engagement_shares', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('engagement_comments', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('engagement_views', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('s3_raw_key', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('platform', 'platform_post_id')
    )
    
    # Create classifications table
    op.create_table('classifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nine_p_product', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('nine_p_place', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('nine_p_price', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('nine_p_publicity', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('nine_p_postconsumption', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('nine_p_purpose', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('nine_p_partnerships', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('nine_p_people', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('nine_p_planet', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('sentiment_label', sa.String(length=20), nullable=False),
        sa.Column('sentiment_positive', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('sentiment_neutral', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('sentiment_negative', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('classification_method', sa.String(length=50), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['social_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id')
    )
    
    # Create monthly_aggregates table
    op.create_table('monthly_aggregates',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('total_posts', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('avg_nine_p_product', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_nine_p_place', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_nine_p_price', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_nine_p_publicity', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_nine_p_postconsumption', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_nine_p_purpose', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_nine_p_partnerships', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_nine_p_people', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_nine_p_planet', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('sentiment_positive_count', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('sentiment_neutral_count', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('sentiment_negative_count', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('avg_sentiment_positive', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_sentiment_neutral', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_sentiment_negative', sa.Numeric(precision=4, scale=3), server_default=sa.text('0.0'), nullable=True),
        sa.Column('total_engagement_likes', sa.BigInteger(), server_default=sa.text('0'), nullable=True),
        sa.Column('total_engagement_shares', sa.BigInteger(), server_default=sa.text('0'), nullable=True),
        sa.Column('total_engagement_comments', sa.BigInteger(), server_default=sa.text('0'), nullable=True),
        sa.Column('total_engagement_views', sa.BigInteger(), server_default=sa.text('0'), nullable=True),
        sa.Column('avg_engagement_likes', sa.Numeric(precision=8, scale=2), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_engagement_shares', sa.Numeric(precision=8, scale=2), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_engagement_comments', sa.Numeric(precision=8, scale=2), server_default=sa.text('0.0'), nullable=True),
        sa.Column('avg_engagement_views', sa.Numeric(precision=8, scale=2), server_default=sa.text('0.0'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('brand_id', 'platform', 'year', 'month')
    )
    
    # Create indexes
    op.create_index('idx_social_posts_brand_id', 'social_posts', ['brand_id'])
    op.create_index('idx_social_posts_platform', 'social_posts', ['platform'])
    op.create_index('idx_social_posts_posted_at', 'social_posts', ['posted_at'])
    op.create_index('idx_social_posts_platform_post_id', 'social_posts', ['platform_post_id'])
    op.create_index('idx_social_posts_text_gin', 'social_posts', ['text'], postgresql_using='gin', postgresql_ops={'text': 'gin_trgm_ops'})
    
    op.create_index('idx_classifications_post_id', 'classifications', ['post_id'])
    op.create_index('idx_classifications_sentiment_label', 'classifications', ['sentiment_label'])
    op.create_index('idx_classifications_confidence_score', 'classifications', ['confidence_score'])
    op.create_index('idx_classifications_method', 'classifications', ['classification_method'])
    
    op.create_index('idx_monthly_aggregates_brand_platform', 'monthly_aggregates', ['brand_id', 'platform'])
    op.create_index('idx_monthly_aggregates_year_month', 'monthly_aggregates', ['year', 'month'])
    
    # Create composite indexes
    op.create_index('idx_social_posts_brand_platform_date', 'social_posts', ['brand_id', 'platform', 'posted_at'])
    op.create_index('idx_classifications_sentiment_confidence', 'classifications', ['sentiment_label', 'confidence_score'])
    
    # Create triggers for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER update_social_posts_updated_at BEFORE UPDATE ON social_posts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER update_classifications_updated_at BEFORE UPDATE ON classifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER update_monthly_aggregates_updated_at BEFORE UPDATE ON monthly_aggregates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    
    # Insert sample brands
    op.execute("""
        INSERT INTO brands (name, description, industry, website_url) VALUES
        ('TechCorp', 'Leading technology company', 'Technology', 'https://techcorp.com'),
        ('FashionBrand', 'Premium fashion retailer', 'Fashion', 'https://fashionbrand.com'),
        ('FoodChain', 'Global restaurant chain', 'Food & Beverage', 'https://foodchain.com')
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_monthly_aggregates_updated_at ON monthly_aggregates;")
    op.execute("DROP TRIGGER IF EXISTS update_classifications_updated_at ON classifications;")
    op.execute("DROP TRIGGER IF EXISTS update_social_posts_updated_at ON social_posts;")
    op.execute("DROP TRIGGER IF EXISTS update_brands_updated_at ON brands;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop indexes
    op.drop_index('idx_classifications_sentiment_confidence', table_name='classifications')
    op.drop_index('idx_social_posts_brand_platform_date', table_name='social_posts')
    op.drop_index('idx_monthly_aggregates_year_month', table_name='monthly_aggregates')
    op.drop_index('idx_monthly_aggregates_brand_platform', table_name='monthly_aggregates')
    op.drop_index('idx_classifications_method', table_name='classifications')
    op.drop_index('idx_classifications_confidence_score', table_name='classifications')
    op.drop_index('idx_classifications_sentiment_label', table_name='classifications')
    op.drop_index('idx_classifications_post_id', table_name='classifications')
    op.drop_index('idx_social_posts_text_gin', table_name='social_posts')
    op.drop_index('idx_social_posts_platform_post_id', table_name='social_posts')
    op.drop_index('idx_social_posts_posted_at', table_name='social_posts')
    op.drop_index('idx_social_posts_platform', table_name='social_posts')
    op.drop_index('idx_social_posts_brand_id', table_name='social_posts')
    
    # Drop tables
    op.drop_table('monthly_aggregates')
    op.drop_table('classifications')
    op.drop_table('social_posts')
    op.drop_table('brands')
