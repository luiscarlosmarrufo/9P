"""
Compare Brands page for brand comparison analysis
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

from web.utils.api_client import APIClient


def show_page(api_client: APIClient, filters: Dict[str, Any]):
    """Show the brand comparison page"""
    
    st.header("⚖️ Brand Comparison")
    st.markdown("Compare multiple brands across 9P dimensions and sentiment")
    
    # Brand selection
    st.subheader("🏷️ Select Brands to Compare")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get available brands
        brands = api_client.get_brands()
        brand_options = [brand['name'] for brand in brands]
        
        selected_brands = st.multiselect(
            "Choose brands (max 5):",
            brand_options,
            default=brand_options[:3] if len(brand_options) >= 3 else brand_options,
            max_selections=5
        )
    
    with col2:
        # Comparison period
        comparison_period = st.selectbox(
            "Comparison Period:",
            ["Last 30 days", "Last 3 months", "Last 6 months", "Last year", "Custom"]
        )
        
        if comparison_period == "Custom":
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("Start Date:")
            with col_end:
                end_date = st.date_input("End Date:")
    
    if len(selected_brands) < 2:
        st.warning("Please select at least 2 brands to compare.")
        return
    
    # Get comparison data
    comparison_data = get_brand_comparison_data(api_client, selected_brands, filters)
    
    # Comparison visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 9P Radar Comparison")
        show_nine_p_radar_comparison(comparison_data, selected_brands)
    
    with col2:
        st.subheader("😊 Sentiment Comparison")
        show_sentiment_comparison(comparison_data, selected_brands)
    
    # Volume and engagement comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Post Volume")
        show_volume_comparison(comparison_data, selected_brands)
    
    with col2:
        st.subheader("💬 Engagement Metrics")
        show_engagement_comparison(comparison_data, selected_brands)
    
    # Detailed comparison table
    st.subheader("📋 Detailed Comparison")
    show_detailed_comparison_table(comparison_data, selected_brands)
    
    # Platform breakdown
    st.subheader("🌐 Platform Performance")
    show_platform_comparison(comparison_data, selected_brands)
    
    # Competitive insights
    st.subheader("🎯 Competitive Insights")
    show_competitive_insights(comparison_data, selected_brands)


def get_brand_comparison_data(api_client: APIClient, brands: List[str], filters: Dict[str, Any]) -> Dict[str, Any]:
    """Get comparison data for selected brands"""
    try:
        # Mock comparison data for demonstration
        np.random.seed(42)
        
        comparison_data = {}
        
        for brand in brands:
            # Generate mock data for each brand
            comparison_data[brand] = {
                'nine_p_scores': {
                    'Product': np.random.uniform(0.3, 0.9),
                    'Place': np.random.uniform(0.2, 0.8),
                    'Price': np.random.uniform(0.3, 0.9),
                    'Publicity': np.random.uniform(0.4, 0.95),
                    'Post-consumption': np.random.uniform(0.3, 0.8),
                    'Purpose': np.random.uniform(0.1, 0.7),
                    'Partnerships': np.random.uniform(0.1, 0.6),
                    'People': np.random.uniform(0.3, 0.8),
                    'Planet': np.random.uniform(0.1, 0.7)
                },
                'sentiment_distribution': {
                    'Positive': np.random.randint(30, 60),
                    'Neutral': np.random.randint(25, 45),
                    'Negative': np.random.randint(10, 25)
                },
                'volume_metrics': {
                    'total_posts': np.random.randint(500, 2000),
                    'daily_average': np.random.randint(15, 65),
                    'growth_rate': np.random.uniform(-10, 25)
                },
                'engagement_metrics': {
                    'avg_likes': np.random.randint(20, 150),
                    'avg_shares': np.random.randint(5, 40),
                    'avg_comments': np.random.randint(3, 25),
                    'engagement_rate': np.random.uniform(2, 8)
                },
                'platform_breakdown': {
                    'Twitter': np.random.randint(40, 80),
                    'Reddit': np.random.randint(20, 60)
                }
            }
        
        return comparison_data
        
    except Exception as e:
        st.error(f"Error loading comparison data: {str(e)}")
        return {}


def show_nine_p_radar_comparison(data: Dict[str, Any], brands: List[str]):
    """Show 9P radar chart comparison"""
    try:
        if not data:
            st.warning("No data available")
            return
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1[:len(brands)]
        
        for i, brand in enumerate(brands):
            if brand in data:
                brand_data = data[brand]['nine_p_scores']
                categories = list(brand_data.keys())
                values = list(brand_data.values())
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=brand,
                    line_color=colors[i],
                    fillcolor=colors[i],
                    opacity=0.3
                ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True,
            height=500,
            title="9P Framework Comparison"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating radar comparison: {str(e)}")


def show_sentiment_comparison(data: Dict[str, Any], brands: List[str]):
    """Show sentiment comparison chart"""
    try:
        if not data:
            st.warning("No data available")
            return
        
        # Prepare data for grouped bar chart
        sentiment_data = []
        for brand in brands:
            if brand in data:
                for sentiment, count in data[brand]['sentiment_distribution'].items():
                    sentiment_data.append({
                        'Brand': brand,
                        'Sentiment': sentiment,
                        'Percentage': count
                    })
        
        df = pd.DataFrame(sentiment_data)
        
        fig = px.bar(
            df,
            x='Brand',
            y='Percentage',
            color='Sentiment',
            title='Sentiment Distribution by Brand',
            color_discrete_map={
                'Positive': '#2ecc71',
                'Neutral': '#95a5a6',
                'Negative': '#e74c3c'
            },
            barmode='group'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating sentiment comparison: {str(e)}")


def show_volume_comparison(data: Dict[str, Any], brands: List[str]):
    """Show post volume comparison"""
    try:
        if not data:
            st.warning("No data available")
            return
        
        volume_data = []
        for brand in brands:
            if brand in data:
                metrics = data[brand]['volume_metrics']
                volume_data.append({
                    'Brand': brand,
                    'Total Posts': metrics['total_posts'],
                    'Daily Average': metrics['daily_average'],
                    'Growth Rate (%)': metrics['growth_rate']
                })
        
        df = pd.DataFrame(volume_data)
        
        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add total posts bar
        fig.add_trace(
            go.Bar(
                x=df['Brand'],
                y=df['Total Posts'],
                name='Total Posts',
                marker_color='lightblue'
            ),
            secondary_y=False,
        )
        
        # Add growth rate line
        fig.add_trace(
            go.Scatter(
                x=df['Brand'],
                y=df['Growth Rate (%)'],
                mode='lines+markers',
                name='Growth Rate (%)',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ),
            secondary_y=True,
        )
        
        fig.update_yaxes(title_text="Total Posts", secondary_y=False)
        fig.update_yaxes(title_text="Growth Rate (%)", secondary_y=True)
        
        fig.update_layout(
            title="Post Volume and Growth Comparison",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating volume comparison: {str(e)}")


def show_engagement_comparison(data: Dict[str, Any], brands: List[str]):
    """Show engagement metrics comparison"""
    try:
        if not data:
            st.warning("No data available")
            return
        
        engagement_data = []
        for brand in brands:
            if brand in data:
                metrics = data[brand]['engagement_metrics']
                engagement_data.append({
                    'Brand': brand,
                    'Avg Likes': metrics['avg_likes'],
                    'Avg Shares': metrics['avg_shares'],
                    'Avg Comments': metrics['avg_comments'],
                    'Engagement Rate': metrics['engagement_rate']
                })
        
        df = pd.DataFrame(engagement_data)
        
        # Melt the dataframe for grouped bar chart
        df_melted = df.melt(
            id_vars=['Brand'],
            value_vars=['Avg Likes', 'Avg Shares', 'Avg Comments'],
            var_name='Metric',
            value_name='Count'
        )
        
        fig = px.bar(
            df_melted,
            x='Brand',
            y='Count',
            color='Metric',
            title='Average Engagement Metrics',
            barmode='group'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating engagement comparison: {str(e)}")


def show_detailed_comparison_table(data: Dict[str, Any], brands: List[str]):
    """Show detailed comparison table"""
    try:
        if not data:
            st.warning("No data available")
            return
        
        # Prepare comparison table
        comparison_rows = []
        
        # 9P scores comparison
        nine_p_categories = ['Product', 'Place', 'Price', 'Publicity', 'Post-consumption',
                            'Purpose', 'Partnerships', 'People', 'Planet']
        
        for category in nine_p_categories:
            row = {'Metric': f'9P - {category}'}
            for brand in brands:
                if brand in data:
                    score = data[brand]['nine_p_scores'][category]
                    row[brand] = f"{score:.2f}"
                else:
                    row[brand] = "N/A"
            comparison_rows.append(row)
        
        # Sentiment scores
        for sentiment in ['Positive', 'Neutral', 'Negative']:
            row = {'Metric': f'Sentiment - {sentiment} (%)'}
            for brand in brands:
                if brand in data:
                    percentage = data[brand]['sentiment_distribution'][sentiment]
                    row[brand] = f"{percentage}%"
                else:
                    row[brand] = "N/A"
            comparison_rows.append(row)
        
        # Volume metrics
        volume_metrics = [
            ('Total Posts', 'total_posts'),
            ('Daily Average', 'daily_average'),
            ('Growth Rate (%)', 'growth_rate')
        ]
        
        for metric_name, metric_key in volume_metrics:
            row = {'Metric': metric_name}
            for brand in brands:
                if brand in data:
                    value = data[brand]['volume_metrics'][metric_key]
                    if metric_key == 'growth_rate':
                        row[brand] = f"{value:.1f}%"
                    else:
                        row[brand] = f"{value:,}"
                else:
                    row[brand] = "N/A"
            comparison_rows.append(row)
        
        df = pd.DataFrame(comparison_rows)
        
        # Style the dataframe
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Add insights
        st.markdown("### 📊 Key Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Find best performing brand in each 9P category
            st.markdown("**🏆 Category Leaders:**")
            for category in nine_p_categories:
                best_brand = max(brands, key=lambda b: data[b]['nine_p_scores'][category] if b in data else 0)
                best_score = data[best_brand]['nine_p_scores'][category] if best_brand in data else 0
                st.write(f"• **{category}**: {best_brand} ({best_score:.2f})")
        
        with col2:
            # Overall sentiment leader
            st.markdown("**😊 Sentiment Leaders:**")
            for sentiment in ['Positive', 'Neutral', 'Negative']:
                best_brand = max(brands, key=lambda b: data[b]['sentiment_distribution'][sentiment] if b in data else 0)
                best_percentage = data[best_brand]['sentiment_distribution'][sentiment] if best_brand in data else 0
                st.write(f"• **{sentiment}**: {best_brand} ({best_percentage}%)")
        
    except Exception as e:
        st.error(f"Error creating comparison table: {str(e)}")


def show_platform_comparison(data: Dict[str, Any], brands: List[str]):
    """Show platform performance comparison"""
    try:
        if not data:
            st.warning("No data available")
            return
        
        platform_data = []
        for brand in brands:
            if brand in data:
                for platform, percentage in data[brand]['platform_breakdown'].items():
                    platform_data.append({
                        'Brand': brand,
                        'Platform': platform,
                        'Percentage': percentage
                    })
        
        df = pd.DataFrame(platform_data)
        
        fig = px.bar(
            df,
            x='Brand',
            y='Percentage',
            color='Platform',
            title='Platform Distribution by Brand',
            color_discrete_map={
                'Twitter': '#1da1f2',
                'Reddit': '#ff4500'
            },
            barmode='stack'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating platform comparison: {str(e)}")


def show_competitive_insights(data: Dict[str, Any], brands: List[str]):
    """Show competitive insights and recommendations"""
    try:
        if not data:
            st.warning("No data available")
            return
        
        st.markdown("### 🎯 Competitive Analysis")
        
        # Calculate overall scores
        overall_scores = {}
        for brand in brands:
            if brand in data:
                nine_p_avg = np.mean(list(data[brand]['nine_p_scores'].values()))
                positive_sentiment = data[brand]['sentiment_distribution']['Positive']
                engagement_rate = data[brand]['engagement_metrics']['engagement_rate']
                
                # Weighted overall score
                overall_score = (nine_p_avg * 0.4) + (positive_sentiment * 0.01 * 0.3) + (engagement_rate * 0.01 * 0.3)
                overall_scores[brand] = overall_score
        
        # Rank brands
        ranked_brands = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🏆 Overall Ranking:**")
            for i, (brand, score) in enumerate(ranked_brands, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                st.write(f"{medal} **{brand}** - Score: {score:.2f}")
        
        with col2:
            st.markdown("**💡 Strategic Recommendations:**")
            
            if len(ranked_brands) >= 2:
                top_brand = ranked_brands[0][0]
                second_brand = ranked_brands[1][0]
                
                # Find strengths and weaknesses
                top_strengths = []
                improvement_areas = []
                
                for category in data[top_brand]['nine_p_scores']:
                    top_score = data[top_brand]['nine_p_scores'][category]
                    if top_score > 0.7:
                        top_strengths.append(category)
                    elif top_score < 0.4:
                        improvement_areas.append(category)
                
                st.write(f"**{top_brand}** strengths:")
                for strength in top_strengths[:3]:
                    st.write(f"• {strength}")
                
                if improvement_areas:
                    st.write(f"**{top_brand}** improvement areas:")
                    for area in improvement_areas[:2]:
                        st.write(f"• {area}")
        
        # Opportunity matrix
        st.markdown("### 🎯 Opportunity Matrix")
        
        opportunity_data = []
        for brand in brands:
            if brand in data:
                # Calculate opportunity score (inverse of current performance)
                nine_p_scores = data[brand]['nine_p_scores']
                for category, score in nine_p_scores.items():
                    opportunity_score = 1 - score  # Higher opportunity where performance is lower
                    opportunity_data.append({
                        'Brand': brand,
                        'Category': category,
                        'Current Score': score,
                        'Opportunity Score': opportunity_score
                    })
        
        df_opportunity = pd.DataFrame(opportunity_data)
        
        # Show top opportunities
        top_opportunities = df_opportunity.nlargest(10, 'Opportunity Score')
        
        fig = px.scatter(
            top_opportunities,
            x='Current Score',
            y='Opportunity Score',
            color='Brand',
            size='Opportunity Score',
            hover_data=['Category'],
            title='Top Improvement Opportunities',
            labels={
                'Current Score': 'Current Performance',
                'Opportunity Score': 'Improvement Potential'
            }
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating competitive insights: {str(e)}")
