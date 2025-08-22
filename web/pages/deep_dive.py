"""
Deep Dive page for detailed analysis with filters
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import numpy as np

from web.utils.api_client import APIClient


def show_page(api_client: APIClient, filters: Dict[str, Any]):
    """Show the deep dive analysis page"""
    
    st.header("🔍 Deep Dive Analysis")
    st.markdown("Detailed analysis with advanced filtering and drill-down capabilities")
    
    # Advanced filters section
    with st.expander("🎛️ Advanced Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sentiment_filter = st.selectbox(
                "Sentiment Filter:",
                ["All", "Positive", "Neutral", "Negative"]
            )
            
            confidence_threshold = st.slider(
                "Min Confidence Score:",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1
            )
        
        with col2:
            nine_p_filter = st.selectbox(
                "9P Category Focus:",
                ["All", "Product", "Place", "Price", "Publicity", 
                 "Post-consumption", "Purpose", "Partnerships", "People", "Planet"]
            )
            
            min_engagement = st.number_input(
                "Min Engagement:",
                min_value=0,
                value=0,
                step=1
            )
        
        with col3:
            classification_stage = st.selectbox(
                "Classification Stage:",
                ["All", "Stage 1 (ML)", "Stage 2 (LLM)"]
            )
            
            text_length = st.selectbox(
                "Text Length:",
                ["All", "Short (<100 chars)", "Medium (100-300)", "Long (>300)"]
            )
    
    # Apply filters and get data
    filtered_data = get_filtered_data(api_client, filters, {
        'sentiment': sentiment_filter,
        'confidence_threshold': confidence_threshold,
        'nine_p_filter': nine_p_filter,
        'min_engagement': min_engagement,
        'classification_stage': classification_stage,
        'text_length': text_length
    })
    
    # Main analysis sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 9P Heatmap")
        show_nine_p_heatmap(filtered_data)
    
    with col2:
        st.subheader("🎯 Sentiment vs Engagement")
        show_sentiment_engagement_scatter(filtered_data)
    
    # Detailed tables section
    st.subheader("📋 Detailed Data View")
    show_detailed_table(api_client, filtered_data, filters)
    
    # Text analysis section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔤 Keyword Analysis")
        show_keyword_analysis(filtered_data)
    
    with col2:
        st.subheader("📈 Classification Confidence")
        show_confidence_distribution(filtered_data)
    
    # Bigrams and n-grams
    st.subheader("🔗 Bigram Analysis")
    show_bigram_analysis(filtered_data)


def get_filtered_data(api_client: APIClient, base_filters: Dict[str, Any], advanced_filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get filtered data based on all applied filters"""
    try:
        # Mock filtered data for demonstration
        np.random.seed(42)
        
        # Generate mock data that respects filters
        data = []
        for i in range(200):
            sentiment_labels = ['Positive', 'Neutral', 'Negative']
            sentiment = np.random.choice(sentiment_labels, p=[0.45, 0.35, 0.2])
            
            # Skip if sentiment filter doesn't match
            if advanced_filters['sentiment'] != 'All' and sentiment != advanced_filters['sentiment']:
                continue
            
            confidence = np.random.uniform(0.3, 0.95)
            if confidence < advanced_filters['confidence_threshold']:
                continue
            
            engagement = np.random.poisson(50)
            if engagement < advanced_filters['min_engagement']:
                continue
            
            # Generate 9P scores
            nine_p_scores = {
                'Product': np.random.uniform(0, 1),
                'Place': np.random.uniform(0, 1),
                'Price': np.random.uniform(0, 1),
                'Publicity': np.random.uniform(0, 1),
                'Post-consumption': np.random.uniform(0, 1),
                'Purpose': np.random.uniform(0, 1),
                'Partnerships': np.random.uniform(0, 1),
                'People': np.random.uniform(0, 1),
                'Planet': np.random.uniform(0, 1)
            }
            
            data.append({
                'id': f'post_{i}',
                'text': f'Sample social media post {i} with various content...',
                'platform': np.random.choice(['Twitter', 'Reddit']),
                'sentiment': sentiment,
                'confidence': confidence,
                'engagement': engagement,
                'nine_p_scores': nine_p_scores,
                'stage': np.random.choice([1, 2], p=[0.7, 0.3]),
                'posted_at': datetime.now() - timedelta(days=np.random.randint(0, 30))
            })
        
        return data
        
    except Exception as e:
        st.error(f"Error loading filtered data: {str(e)}")
        return []


def show_nine_p_heatmap(data: List[Dict[str, Any]]):
    """Show 9P scores as a heatmap"""
    try:
        if not data:
            st.warning("No data available for the selected filters")
            return
        
        # Aggregate 9P scores
        nine_p_categories = ['Product', 'Place', 'Price', 'Publicity', 'Post-consumption',
                            'Purpose', 'Partnerships', 'People', 'Planet']
        
        # Create matrix for heatmap
        sentiment_categories = ['Positive', 'Neutral', 'Negative']
        heatmap_data = []
        
        for sentiment in sentiment_categories:
            sentiment_data = [item for item in data if item['sentiment'] == sentiment]
            if sentiment_data:
                avg_scores = []
                for category in nine_p_categories:
                    scores = [item['nine_p_scores'][category] for item in sentiment_data]
                    avg_scores.append(np.mean(scores))
                heatmap_data.append(avg_scores)
            else:
                heatmap_data.append([0] * len(nine_p_categories))
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=nine_p_categories,
            y=sentiment_categories,
            colorscale='RdYlBu_r',
            text=[[f'{val:.2f}' for val in row] for row in heatmap_data],
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="9P Scores by Sentiment",
            xaxis_title="9P Categories",
            yaxis_title="Sentiment",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")


def show_sentiment_engagement_scatter(data: List[Dict[str, Any]]):
    """Show sentiment vs engagement scatter plot"""
    try:
        if not data:
            st.warning("No data available for the selected filters")
            return
        
        df = pd.DataFrame([
            {
                'engagement': item['engagement'],
                'confidence': item['confidence'],
                'sentiment': item['sentiment'],
                'platform': item['platform']
            }
            for item in data
        ])
        
        fig = px.scatter(
            df,
            x='confidence',
            y='engagement',
            color='sentiment',
            symbol='platform',
            title='Engagement vs Classification Confidence',
            labels={
                'confidence': 'Classification Confidence',
                'engagement': 'Engagement Score'
            },
            color_discrete_map={
                'Positive': '#2ecc71',
                'Neutral': '#95a5a6',
                'Negative': '#e74c3c'
            }
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating scatter plot: {str(e)}")


def show_detailed_table(api_client: APIClient, data: List[Dict[str, Any]], filters: Dict[str, Any]):
    """Show detailed data table with drill-down capabilities"""
    try:
        if not data:
            st.warning("No data available for the selected filters")
            return
        
        # Prepare table data
        table_data = []
        for item in data:
            # Get top 9P category
            top_9p = max(item['nine_p_scores'], key=item['nine_p_scores'].get)
            top_9p_score = item['nine_p_scores'][top_9p]
            
            table_data.append({
                'ID': item['id'],
                'Text Preview': item['text'][:100] + '...',
                'Platform': item['platform'],
                'Sentiment': item['sentiment'],
                'Top 9P': f"{top_9p} ({top_9p_score:.2f})",
                'Confidence': f"{item['confidence']:.2f}",
                'Engagement': item['engagement'],
                'Stage': f"Stage {item['stage']}",
                'Date': item['posted_at'].strftime('%Y-%m-%d')
            })
        
        df = pd.DataFrame(table_data)
        
        # Add pagination
        page_size = 20
        total_pages = len(df) // page_size + (1 if len(df) % page_size > 0 else 0)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.selectbox(
                f"Page (showing {len(df)} items):",
                range(1, total_pages + 1),
                index=0
            )
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Display table
        st.dataframe(
            df.iloc[start_idx:end_idx],
            use_container_width=True,
            hide_index=True
        )
        
        # Item detail drill-down
        if st.button("🔍 View Item Details"):
            selected_id = st.selectbox("Select item to view:", df['ID'].tolist())
            if selected_id:
                show_item_detail(api_client, selected_id)
        
    except Exception as e:
        st.error(f"Error showing detailed table: {str(e)}")


def show_item_detail(api_client: APIClient, item_id: str):
    """Show detailed view of a specific item"""
    try:
        with st.expander(f"📄 Item Details: {item_id}", expanded=True):
            # Mock detailed item data
            item_detail = {
                'id': item_id,
                'text': 'This is a detailed view of the social media post with full content and analysis...',
                'platform': 'Twitter',
                'author': '@example_user',
                'posted_at': '2024-01-15 14:30:00',
                'engagement': {'likes': 45, 'shares': 12, 'comments': 8},
                'nine_p_scores': {
                    'Product': 0.75, 'Place': 0.23, 'Price': 0.45, 'Publicity': 0.89,
                    'Post-consumption': 0.34, 'Purpose': 0.12, 'Partnerships': 0.67,
                    'People': 0.56, 'Planet': 0.28
                },
                'sentiment': {'positive': 0.78, 'neutral': 0.15, 'negative': 0.07},
                'classification_stage': 2,
                'confidence': 0.85,
                'llm_reasoning': 'This post primarily discusses marketing campaigns and promotional activities...'
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Full Text:**")
                st.write(item_detail['text'])
                
                st.write("**Metadata:**")
                st.write(f"Platform: {item_detail['platform']}")
                st.write(f"Author: {item_detail['author']}")
                st.write(f"Posted: {item_detail['posted_at']}")
                
                st.write("**Engagement:**")
                for key, value in item_detail['engagement'].items():
                    st.write(f"{key.title()}: {value}")
            
            with col2:
                st.write("**9P Classification:**")
                for category, score in item_detail['nine_p_scores'].items():
                    st.progress(score, text=f"{category}: {score:.2f}")
                
                st.write("**Sentiment Analysis:**")
                for sentiment, score in item_detail['sentiment'].items():
                    st.progress(score, text=f"{sentiment.title()}: {score:.2f}")
                
                if item_detail.get('llm_reasoning'):
                    st.write("**LLM Reasoning:**")
                    st.write(item_detail['llm_reasoning'])
        
    except Exception as e:
        st.error(f"Error showing item detail: {str(e)}")


def show_keyword_analysis(data: List[Dict[str, Any]]):
    """Show keyword frequency analysis"""
    try:
        # Mock keyword data
        keywords = {
            'product': 45, 'quality': 38, 'service': 32, 'price': 28, 'experience': 25,
            'customer': 22, 'brand': 20, 'support': 18, 'value': 16, 'recommend': 14
        }
        
        df = pd.DataFrame(list(keywords.items()), columns=['Keyword', 'Frequency'])
        
        fig = px.bar(
            df,
            x='Frequency',
            y='Keyword',
            orientation='h',
            title='Top Keywords',
            color='Frequency',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error showing keyword analysis: {str(e)}")


def show_confidence_distribution(data: List[Dict[str, Any]]):
    """Show classification confidence distribution"""
    try:
        if not data:
            st.warning("No data available")
            return
        
        confidences = [item['confidence'] for item in data]
        
        fig = go.Figure(data=[go.Histogram(
            x=confidences,
            nbinsx=20,
            marker_color='lightblue',
            opacity=0.7
        )])
        
        fig.update_layout(
            title='Classification Confidence Distribution',
            xaxis_title='Confidence Score',
            yaxis_title='Count',
            height=400
        )
        
        # Add vertical line for threshold
        fig.add_vline(
            x=0.7,
            line_dash="dash",
            line_color="red",
            annotation_text="Threshold"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error showing confidence distribution: {str(e)}")


def show_bigram_analysis(data: List[Dict[str, Any]]):
    """Show bigram analysis"""
    try:
        # Mock bigram data
        bigrams = [
            ('customer', 'service', 28),
            ('great', 'product', 25),
            ('highly', 'recommend', 22),
            ('good', 'quality', 20),
            ('fast', 'delivery', 18),
            ('excellent', 'experience', 16),
            ('competitive', 'price', 14),
            ('friendly', 'staff', 12),
            ('easy', 'use', 10),
            ('value', 'money', 8)
        ]
        
        df = pd.DataFrame(bigrams, columns=['Word 1', 'Word 2', 'Frequency'])
        df['Bigram'] = df['Word 1'] + ' + ' + df['Word 2']
        
        fig = px.bar(
            df,
            x='Frequency',
            y='Bigram',
            orientation='h',
            title='Most Common Bigrams',
            color='Frequency',
            color_continuous_scale='Greens'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error showing bigram analysis: {str(e)}")
