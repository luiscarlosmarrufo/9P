"""
Exports page for data export functionality
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
import io

from web.utils.api_client import APIClient


def show_page(api_client: APIClient, filters: Dict[str, Any]):
    """Show the exports page"""
    
    st.header("📤 Data Exports")
    st.markdown("Export your social media analytics data in various formats")
    
    # Export configuration
    st.subheader("⚙️ Export Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export format
        export_format = st.selectbox(
            "Export Format:",
            ["CSV", "JSON", "Excel"],
            help="Choose the format for your data export"
        )
        
        # Date range
        st.markdown("**Date Range:**")
        date_range_option = st.radio(
            "Select range:",
            ["Last 7 days", "Last 30 days", "Last 3 months", "Custom range"],
            horizontal=True
        )
        
        if date_range_option == "Custom range":
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("Start Date:")
            with col_end:
                end_date = st.date_input("End Date:")
        else:
            days_map = {
                "Last 7 days": 7,
                "Last 30 days": 30,
                "Last 3 months": 90
            }
            days = days_map[date_range_option]
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
    
    with col2:
        # Brand filter
        brands = api_client.get_brands()
        brand_options = ["All Brands"] + [brand['name'] for brand in brands]
        selected_brand = st.selectbox("Brand:", brand_options)
        
        # Platform filter
        platform_options = ["All Platforms", "Twitter", "Reddit"]
        selected_platform = st.selectbox("Platform:", platform_options)
        
        # Data options
        st.markdown("**Include in Export:**")
        include_raw_data = st.checkbox("Raw social media data", value=False)
        include_classifications = st.checkbox("9P classifications", value=True)
        include_sentiment = st.checkbox("Sentiment analysis", value=True)
        include_engagement = st.checkbox("Engagement metrics", value=True)
        include_metadata = st.checkbox("Post metadata", value=True)
    
    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Filters
            sentiment_filter = st.selectbox(
                "Sentiment Filter:",
                ["All", "Positive", "Neutral", "Negative"]
            )
            
            min_confidence = st.slider(
                "Minimum Confidence Score:",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1
            )
        
        with col2:
            # Limits
            max_records = st.number_input(
                "Maximum Records:",
                min_value=100,
                max_value=100000,
                value=10000,
                step=100,
                help="Limit the number of records to export"
            )
            
            # Sampling
            use_sampling = st.checkbox(
                "Use random sampling",
                help="Randomly sample data if dataset is large"
            )
    
    # Preview section
    st.subheader("👀 Data Preview")
    
    if st.button("🔍 Generate Preview", type="secondary"):
        show_data_preview(api_client, {
            'brand': selected_brand if selected_brand != "All Brands" else None,
            'platform': selected_platform.lower() if selected_platform != "All Platforms" else None,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'sentiment': sentiment_filter if sentiment_filter != "All" else None,
            'min_confidence': min_confidence,
            'limit': min(max_records, 100)  # Limit preview to 100 records
        })
    
    # Export section
    st.subheader("📥 Generate Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Data", type="primary"):
            export_data(api_client, {
                'format': export_format.lower(),
                'brand': selected_brand if selected_brand != "All Brands" else None,
                'platform': selected_platform.lower() if selected_platform != "All Platforms" else None,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'include_raw_data': include_raw_data,
                'include_classifications': include_classifications,
                'max_records': max_records
            })
    
    with col2:
        if st.button("📋 Export Summary Report"):
            export_summary_report(api_client, {
                'brand': selected_brand if selected_brand != "All Brands" else None,
                'platform': selected_platform.lower() if selected_platform != "All Platforms" else None,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            })
    
    with col3:
        if st.button("📈 Export Analytics Dashboard"):
            export_analytics_dashboard({
                'brand': selected_brand if selected_brand != "All Brands" else None,
                'platform': selected_platform.lower() if selected_platform != "All Platforms" else None,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            })
    
    # Export history
    st.subheader("📜 Export History")
    show_export_history()
    
    # Scheduled exports
    st.subheader("⏰ Scheduled Exports")
    show_scheduled_exports()


def show_data_preview(api_client: APIClient, export_params: Dict[str, Any]):
    """Show a preview of the data to be exported"""
    try:
        with st.spinner("Generating preview..."):
            # Get sample data
            items_response = api_client.get_items(
                brand_id=export_params.get('brand'),
                platform=export_params.get('platform'),
                sentiment=export_params.get('sentiment'),
                start_date=export_params.get('start_date'),
                end_date=export_params.get('end_date'),
                limit=export_params.get('limit', 100)
            )
            
            if not items_response.get('items'):
                st.warning("No data found for the selected criteria.")
                return
            
            items = items_response['items']
            
            # Prepare preview data
            preview_data = []
            for item in items:
                row = {
                    'ID': item['id'],
                    'Platform': item['platform'],
                    'Text': item['text'][:100] + '...' if len(item['text']) > 100 else item['text'],
                    'Sentiment': item['classification']['sentiment']['label'],
                    'Posted Date': item['posted_at'][:10],
                    'Engagement': item['engagement']['likes'] + item['engagement']['shares'] + item['engagement']['comments']
                }
                
                # Add 9P scores
                nine_p = item['classification']['nine_p']
                top_9p = max(nine_p, key=nine_p.get)
                row['Top 9P'] = f"{top_9p} ({nine_p[top_9p]:.2f})"
                
                preview_data.append(row)
            
            df = pd.DataFrame(preview_data)
            
            # Show preview
            st.success(f"Preview: {len(df)} records found")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Show summary statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", len(df))
            
            with col2:
                sentiment_counts = df['Sentiment'].value_counts()
                most_common_sentiment = sentiment_counts.index[0] if len(sentiment_counts) > 0 else "N/A"
                st.metric("Most Common Sentiment", most_common_sentiment)
            
            with col3:
                avg_engagement = df['Engagement'].mean() if len(df) > 0 else 0
                st.metric("Avg Engagement", f"{avg_engagement:.1f}")
    
    except Exception as e:
        st.error(f"Error generating preview: {str(e)}")


def export_data(api_client: APIClient, export_params: Dict[str, Any]):
    """Export data based on parameters"""
    try:
        with st.spinner("Generating export..."):
            # Call API export endpoint
            response = api_client.export_data(**export_params)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            brand_suffix = f"_{export_params.get('brand', 'all_brands').replace(' ', '_')}"
            platform_suffix = f"_{export_params.get('platform', 'all_platforms')}"
            filename = f"9p_export{brand_suffix}{platform_suffix}_{timestamp}.{export_params['format']}"
            
            # Provide download
            st.download_button(
                label=f"📥 Download {export_params['format'].upper()} Export",
                data=response.content,
                file_name=filename,
                mime=get_mime_type(export_params['format'])
            )
            
            st.success(f"Export generated successfully! Click the download button above to save your file.")
            
            # Log export
            log_export(export_params, filename)
    
    except Exception as e:
        st.error(f"Error generating export: {str(e)}")


def export_summary_report(api_client: APIClient, export_params: Dict[str, Any]):
    """Export a summary report"""
    try:
        with st.spinner("Generating summary report..."):
            # Mock summary report data
            report_data = {
                'report_title': '9P Social Analytics Summary Report',
                'generated_at': datetime.now().isoformat(),
                'period': f"{export_params['start_date']} to {export_params['end_date']}",
                'brand': export_params.get('brand', 'All Brands'),
                'platform': export_params.get('platform', 'All Platforms'),
                'summary_metrics': {
                    'total_posts': 1250,
                    'avg_daily_posts': 42,
                    'sentiment_distribution': {'positive': 45, 'neutral': 35, 'negative': 20},
                    'top_9p_categories': ['Publicity', 'Product', 'People'],
                    'engagement_rate': 3.2
                },
                'key_insights': [
                    'Publicity mentions increased 23% compared to previous period',
                    'Positive sentiment improved by 5 percentage points',
                    'Twitter engagement outperformed Reddit by 15%',
                    'Product-related discussions peaked mid-month'
                ]
            }
            
            # Convert to formatted text
            report_text = format_summary_report(report_data)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"9p_summary_report_{timestamp}.txt"
            
            st.download_button(
                label="📋 Download Summary Report",
                data=report_text,
                file_name=filename,
                mime="text/plain"
            )
            
            st.success("Summary report generated successfully!")
    
    except Exception as e:
        st.error(f"Error generating summary report: {str(e)}")


def export_analytics_dashboard(export_params: Dict[str, Any]):
    """Export an analytics dashboard as HTML"""
    try:
        with st.spinner("Generating analytics dashboard..."):
            # Mock dashboard HTML
            dashboard_html = generate_dashboard_html(export_params)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"9p_dashboard_{timestamp}.html"
            
            st.download_button(
                label="📈 Download Analytics Dashboard",
                data=dashboard_html,
                file_name=filename,
                mime="text/html"
            )
            
            st.success("Analytics dashboard generated successfully!")
    
    except Exception as e:
        st.error(f"Error generating dashboard: {str(e)}")


def show_export_history():
    """Show export history"""
    # Mock export history
    history = [
        {
            'timestamp': datetime.now() - timedelta(hours=2),
            'type': 'CSV Export',
            'records': 1250,
            'brand': 'Brand A',
            'status': 'Completed'
        },
        {
            'timestamp': datetime.now() - timedelta(days=1),
            'type': 'Summary Report',
            'records': 890,
            'brand': 'All Brands',
            'status': 'Completed'
        },
        {
            'timestamp': datetime.now() - timedelta(days=3),
            'type': 'JSON Export',
            'records': 2100,
            'brand': 'Brand B',
            'status': 'Completed'
        }
    ]
    
    for export in history:
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write(f"**{export['type']}**")
                st.write(export['timestamp'].strftime('%Y-%m-%d %H:%M'))
            
            with col2:
                st.write(f"Records: {export['records']:,}")
                st.write(f"Brand: {export['brand']}")
            
            with col3:
                status_color = "🟢" if export['status'] == 'Completed' else "🟡"
                st.write(f"{status_color} {export['status']}")
            
            with col4:
                if st.button(f"📥 Re-download", key=f"redownload_{export['timestamp']}"):
                    st.info("Re-download functionality would be implemented here")
            
            st.divider()


def show_scheduled_exports():
    """Show and manage scheduled exports"""
    st.markdown("Set up automatic exports to run on a schedule")
    
    with st.expander("➕ Create New Scheduled Export"):
        col1, col2 = st.columns(2)
        
        with col1:
            schedule_name = st.text_input("Schedule Name:")
            export_format = st.selectbox("Format:", ["CSV", "JSON"])
            frequency = st.selectbox("Frequency:", ["Daily", "Weekly", "Monthly"])
        
        with col2:
            brand_filter = st.selectbox("Brand:", ["All Brands", "Brand A", "Brand B"])
            platform_filter = st.selectbox("Platform:", ["All Platforms", "Twitter", "Reddit"])
            email_recipients = st.text_area("Email Recipients (one per line):")
        
        if st.button("📅 Create Schedule"):
            st.success(f"Scheduled export '{schedule_name}' created successfully!")
    
    # Show existing schedules
    st.markdown("**Current Schedules:**")
    
    schedules = [
        {
            'name': 'Weekly Brand A Report',
            'format': 'CSV',
            'frequency': 'Weekly',
            'next_run': datetime.now() + timedelta(days=3),
            'status': 'Active'
        },
        {
            'name': 'Monthly Summary',
            'format': 'JSON',
            'frequency': 'Monthly',
            'next_run': datetime.now() + timedelta(days=15),
            'status': 'Active'
        }
    ]
    
    for schedule in schedules:
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write(f"**{schedule['name']}**")
                st.write(f"{schedule['format']} • {schedule['frequency']}")
            
            with col2:
                st.write("Next Run:")
                st.write(schedule['next_run'].strftime('%Y-%m-%d %H:%M'))
            
            with col3:
                status_color = "🟢" if schedule['status'] == 'Active' else "🔴"
                st.write(f"{status_color} {schedule['status']}")
            
            with col4:
                if st.button("⚙️ Edit", key=f"edit_{schedule['name']}"):
                    st.info("Edit functionality would be implemented here")
                if st.button("🗑️ Delete", key=f"delete_{schedule['name']}"):
                    st.warning("Delete functionality would be implemented here")
            
            st.divider()


def get_mime_type(format: str) -> str:
    """Get MIME type for export format"""
    mime_types = {
        'csv': 'text/csv',
        'json': 'application/json',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    return mime_types.get(format.lower(), 'application/octet-stream')


def format_summary_report(data: Dict[str, Any]) -> str:
    """Format summary report data as text"""
    report = f"""
{data['report_title']}
{'=' * len(data['report_title'])}

Generated: {data['generated_at']}
Period: {data['period']}
Brand: {data['brand']}
Platform: {data['platform']}

SUMMARY METRICS
---------------
Total Posts: {data['summary_metrics']['total_posts']:,}
Average Daily Posts: {data['summary_metrics']['avg_daily_posts']}
Engagement Rate: {data['summary_metrics']['engagement_rate']}%

SENTIMENT DISTRIBUTION
----------------------
Positive: {data['summary_metrics']['sentiment_distribution']['positive']}%
Neutral: {data['summary_metrics']['sentiment_distribution']['neutral']}%
Negative: {data['summary_metrics']['sentiment_distribution']['negative']}%

TOP 9P CATEGORIES
-----------------
{', '.join(data['summary_metrics']['top_9p_categories'])}

KEY INSIGHTS
------------
"""
    
    for i, insight in enumerate(data['key_insights'], 1):
        report += f"{i}. {insight}\n"
    
    return report


def generate_dashboard_html(params: Dict[str, Any]) -> str:
    """Generate HTML dashboard"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>9P Analytics Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #1f77b4; color: white; padding: 20px; text-align: center; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f0f2f6; border-radius: 5px; }}
        .chart {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>9P Social Analytics Dashboard</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <h3>Total Posts</h3>
            <h2>1,250</h2>
        </div>
        <div class="metric">
            <h3>Positive Sentiment</h3>
            <h2>45%</h2>
        </div>
        <div class="metric">
            <h3>Engagement Rate</h3>
            <h2>3.2%</h2>
        </div>
    </div>
    
    <div class="chart">
        <h3>9P Distribution</h3>
        <p>Interactive charts would be embedded here using libraries like Chart.js or D3.js</p>
    </div>
    
    <div class="chart">
        <h3>Sentiment Trends</h3>
        <p>Time series sentiment analysis would be displayed here</p>
    </div>
</body>
</html>
"""


def log_export(params: Dict[str, Any], filename: str):
    """Log export activity"""
    # In a real implementation, this would log to a database or file
    pass
