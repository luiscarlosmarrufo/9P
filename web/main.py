"""
Main Streamlit application for 9P Social Analytics Dashboard
"""

import streamlit as st
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.pages import overview, deep_dive, compare_brands, exports
from web.utils.auth import check_authentication
from web.utils.api_client import APIClient
from control.core.config import settings

# Page configuration
st.set_page_config(
    page_title="9P Social Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .sidebar-section {
        margin-bottom: 2rem;
    }
    .filter-section {
        background-color: #fafafa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Authentication check (if enabled)
    if not settings.DEBUG:
        if not check_authentication():
            st.stop()
    
    # Initialize API client
    api_client = APIClient()
    
    # Sidebar navigation
    st.sidebar.markdown("# 9P Analytics")
    st.sidebar.markdown("---")
    
    # Page selection
    pages = {
        "📈 Overview": "overview",
        "🔍 Deep Dive": "deep_dive", 
        "⚖️ Compare Brands": "compare_brands",
        "📤 Exports": "exports"
    }
    
    selected_page = st.sidebar.selectbox(
        "Navigate to:",
        list(pages.keys()),
        index=0
    )
    
    page_key = pages[selected_page]
    
    # Global filters in sidebar
    st.sidebar.markdown("## 🎛️ Global Filters")
    
    with st.sidebar.container():
        # Brand filter
        brands = api_client.get_brands()
        brand_options = ["All Brands"] + [brand['name'] for brand in brands]
        selected_brand = st.selectbox("Brand:", brand_options)
        
        # Platform filter
        platform_options = ["All Platforms", "Twitter", "Reddit"]
        selected_platform = st.selectbox("Platform:", platform_options)
        
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date:",
                value=datetime.now() - timedelta(days=30),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "End Date:",
                value=datetime.now(),
                max_value=datetime.now()
            )
        
        # Language filter
        language_options = ["All Languages", "English", "Spanish", "French", "German"]
        selected_language = st.selectbox("Language:", language_options)
        
        # Apply filters button
        if st.button("🔄 Apply Filters", type="primary"):
            st.rerun()
    
    # Build filter context
    filters = {
        'brand': selected_brand if selected_brand != "All Brands" else None,
        'platform': selected_platform.lower() if selected_platform != "All Platforms" else None,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'language': selected_language if selected_language != "All Languages" else None
    }
    
    # System status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔧 System Status")
    
    try:
        health = api_client.get_health()
        if health['status'] == 'healthy':
            st.sidebar.success("✅ System Healthy")
        else:
            st.sidebar.error("❌ System Issues")
            
        # Show basic metrics
        metrics = api_client.get_metrics()
        st.sidebar.metric("Total Posts", f"{metrics['total_posts']:,}")
        st.sidebar.metric("Processed", f"{metrics['processed_posts']:,}")
        
    except Exception as e:
        st.sidebar.error(f"❌ API Connection Error: {str(e)}")
    
    # Main content area
    st.markdown('<div class="main-header">9P Social Analytics Platform</div>', unsafe_allow_html=True)
    
    # Route to selected page
    if page_key == "overview":
        overview.show_page(api_client, filters)
    elif page_key == "deep_dive":
        deep_dive.show_page(api_client, filters)
    elif page_key == "compare_brands":
        compare_brands.show_page(api_client, filters)
    elif page_key == "exports":
        exports.show_page(api_client, filters)
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #666;'>"
        f"9P Social Analytics Platform v{settings.APP_VERSION} | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f"</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
