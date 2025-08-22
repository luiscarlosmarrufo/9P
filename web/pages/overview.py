"""
Overview page for the 9P Social Analytics Dashboard
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any

from web.utils.api_client import APIClient, get_cached_metrics, get_cached_summary


def show_page(api_client: APIClient, filters: Dict[str, Any]):
    """Show the overview page"""
    
    st.header("📈 Overview Dashboard")
    st.markdown("High-level metrics and trends for social media analytics")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        metrics = get_cached_metrics(api_client)
        
        with col1:
            st.metric(
                "Total Posts",
                f"{metrics['total_posts']:,}",
                delta=f"+{metrics.get('posts_growth', 0):,}"
            )
        
        with col2:
            processing_rate = (metrics['processed_posts'] / max(metrics['total_posts'], 1)) * 100
            st.metric(
                "Processing Rate",
                f"{processing_rate:.1f}%",
                delta=f"{metrics.get('processing_growth', 0):.1f}%"
            )
        
        with col3:
            st.metric(
                "Active Brands",
                f"{metrics['active_brands']:,}",
                delta=f"+{metrics.get('brands_growth', 0):,}"
            )
        
        with col4:
            st.metric(
                "Storage Usage",
                f"{metrics['storage_usage_gb']:.1f} GB",
                delta=f"+{metrics.get('storage_growth', 0):.1f} GB"
            )
    
    except Exception as e:
        st.error(f"Error loading metrics: {str(e)}")
        return
    
    st.markdown("---")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 9P Distribution")
        show_nine_p_distribution(api_client, filters)
    
    with col2:
        st.subheader("😊 Sentiment Analysis")
        show_sentiment_distribution(api_client, filters)
    
    # Time series section
    st.subheader("📈 Trends Over Time")
    show_time_series(api_client, filters)
    
    # Platform comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌐 Platform Breakdown")
        show_platform_breakdown(api_client, filters)
    
    with col2:
        st.subheader("🔥 Top Performing Content")
        show_top_content(api_client, filters)
    
    # Recent activity
    st.subheader("🕒 Recent Activity")
    show_recent_activity(api_client, filters)


def show_nine_p_distribution(api_client: APIClient, filters: Dict[str, Any]):
    """Show 9P framework distribution"""
    try:
        # Mock data for demonstration
        nine_p_data = {
            'Product': 0.65,
            'Place': 0.45,
            'Price': 0.55,
            'Publicity': 0.70,
            'Post-consumption': 0.60,
            'Purpose': 0.35,
            'Partnerships': 0.25,
            'People': 0.50,
            'Planet': 0.30
        }
        
        # Create radar chart
        categories = list(nine_p_data.keys())
        values = list(nine_p_data.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='9P Scores',
            line_color='#1f77b4'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading 9P distribution: {str(e)}")


def show_sentiment_distribution(api_client: APIClient, filters: Dict[str, Any]):
    """Show sentiment distribution"""
    try:
        # Mock data for demonstration
        sentiment_data = {
            'Positive': 45,
            'Neutral': 35,
            'Negative': 20
        }
        
        colors = ['#2ecc71', '#95a5a6', '#e74c3c']
        
        fig = go.Figure(data=[go.Pie(
            labels=list(sentiment_data.keys()),
            values=list(sentiment_data.values()),
            marker_colors=colors,
            hole=0.4
        )])
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )
        
        fig.update_layout(
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading sentiment distribution: {str(e)}")


def show_time_series(api_client: APIClient, filters: Dict[str, Any]):
    """Show time series trends"""
    try:
        # Mock time series data
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=30),
            end=datetime.now(),
            freq='D'
        )
        
        # Generate mock data
        import numpy as np
        np.random.seed(42)
        
        posts_data = np.random.poisson(50, len(dates))
        sentiment_data = np.random.uniform(0.3, 0.7, len(dates))
        
        df = pd.DataFrame({
            'Date': dates,
            'Posts': posts_data,
            'Avg_Sentiment': sentiment_data
        })
        
        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add posts trace
        fig.add_trace(
            go.Scatter(
                x=df['Date'],
                y=df['Posts'],
                name='Daily Posts',
                line=dict(color='#1f77b4')
            ),
            secondary_y=False,
        )
        
        # Add sentiment trace
        fig.add_trace(
            go.Scatter(
                x=df['Date'],
                y=df['Avg_Sentiment'],
                name='Avg Sentiment',
                line=dict(color='#ff7f0e')
            ),
            secondary_y=True,
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Number of Posts", secondary_y=False)
        fig.update_yaxes(title_text="Average Sentiment Score", secondary_y=True)
        
        fig.update_layout(
            title="Posts and Sentiment Trends",
            xaxis_title="Date",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading time series: {str(e)}")


def show_platform_breakdown(api_client: APIClient, filters: Dict[str, Any]):
    """Show platform breakdown"""
    try:
        # Mock platform data
        platform_data = {
            'Twitter': 65,
            'Reddit': 35
        }
        
        fig = go.Figure(data=[go.Bar(
            x=list(platform_data.keys()),
            y=list(platform_data.values()),
            marker_color=['#1da1f2', '#ff4500']
        )])
        
        fig.update_layout(
            title="Posts by Platform (%)",
            xaxis_title="Platform",
            yaxis_title="Percentage",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading platform breakdown: {str(e)}")


def show_top_content(api_client: APIClient, filters: Dict[str, Any]):
    """Show top performing content"""
    try:
        # Mock top content data
        top_content = [
            {
                'text': 'Amazing product quality! Highly recommend...',
                'platform': 'Twitter',
                'engagement': 245,
                'sentiment': 'Positive'
            },
            {
                'text': 'Great customer service experience today...',
                'platform': 'Reddit',
                'engagement': 189,
                'sentiment': 'Positive'
            },
            {
                'text': 'Love the new sustainable packaging...',
                'platform': 'Twitter',
                'engagement': 156,
                'sentiment': 'Positive'
            },
            {
                'text': 'Price point is very competitive...',
                'platform': 'Reddit',
                'engagement': 134,
                'sentiment': 'Neutral'
            },
            {
                'text': 'Store location is very convenient...',
                'platform': 'Twitter',
                'engagement': 98,
                'sentiment': 'Positive'
            }
        ]
        
        for i, content in enumerate(top_content, 1):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{i}.** {content['text'][:60]}...")
                
                with col2:
                    st.write(f"📱 {content['platform']}")
                    st.write(f"💬 {content['engagement']}")
                
                with col3:
                    sentiment_color = {
                        'Positive': '🟢',
                        'Neutral': '🟡',
                        'Negative': '🔴'
                    }
                    st.write(f"{sentiment_color.get(content['sentiment'], '⚪')} {content['sentiment']}")
                
                if i < len(top_content):
                    st.divider()
        
    except Exception as e:
        st.error(f"Error loading top content: {str(e)}")


def show_recent_activity(api_client: APIClient, filters: Dict[str, Any]):
    """Show recent activity feed"""
    try:
        # Mock recent activity data
        activities = [
            {
                'timestamp': datetime.now() - timedelta(minutes=5),
                'type': 'ingestion',
                'message': 'Completed Twitter ingestion for Brand A (150 new posts)',
                'status': 'success'
            },
            {
                'timestamp': datetime.now() - timedelta(minutes=15),
                'type': 'classification',
                'message': 'Processed 89 posts through Stage 1 classification',
                'status': 'success'
            },
            {
                'timestamp': datetime.now() - timedelta(minutes=32),
                'type': 'ingestion',
                'message': 'Started Reddit ingestion for Brand B',
                'status': 'in_progress'
            },
            {
                'timestamp': datetime.now() - timedelta(hours=1),
                'type': 'aggregation',
                'message': 'Monthly aggregates calculated for December 2024',
                'status': 'success'
            },
            {
                'timestamp': datetime.now() - timedelta(hours=2),
                'type': 'classification',
                'message': 'Stage 2 vLLM classification completed (12 posts)',
                'status': 'success'
            }
        ]
        
        for activity in activities:
            with st.container():
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    st.write(activity['timestamp'].strftime('%H:%M'))
                
                with col2:
                    type_icons = {
                        'ingestion': '📥',
                        'classification': '🤖',
                        'aggregation': '📊'
                    }
                    icon = type_icons.get(activity['type'], '⚙️')
                    st.write(f"{icon} {activity['message']}")
                
                with col3:
                    status_icons = {
                        'success': '✅',
                        'in_progress': '🔄',
                        'failed': '❌'
                    }
                    st.write(status_icons.get(activity['status'], '⚪'))
                
                st.divider()
        
    except Exception as e:
        st.error(f"Error loading recent activity: {str(e)}")


def show_summary_cards(api_client: APIClient, filters: Dict[str, Any]):
    """Show summary cards with key insights"""
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4>🎯 Top 9P Category</h4>
                <h2>Publicity</h2>
                <p>70% of posts mention marketing/advertising</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4>😊 Sentiment Trend</h4>
                <h2>↗️ Improving</h2>
                <p>+5% positive sentiment this month</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h4>🚀 Growth Rate</h4>
                <h2>+23%</h2>
                <p>Monthly post volume increase</p>
            </div>
            """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error loading summary cards: {str(e)}")
