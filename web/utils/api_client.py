"""
API client for Streamlit web application
"""

import requests
import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from control.core.config import settings


class APIClient:
    """Client for communicating with the FastAPI backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client"""
        self.base_url = base_url
        self.api_v1 = f"{base_url}{settings.API_V1_STR}"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.api_v1}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON response: {str(e)}")
            raise
    
    def get_health(self) -> Dict[str, Any]:
        """Get system health status"""
        return self._make_request('GET', '/health')
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return self._make_request('GET', '/metrics')
    
    def get_brands(self) -> List[Dict[str, Any]]:
        """Get list of brands"""
        try:
            # This would be implemented when brand management is added
            # For now, return mock data
            return [
                {'id': '1', 'name': 'Brand A', 'is_active': True},
                {'id': '2', 'name': 'Brand B', 'is_active': True},
                {'id': '3', 'name': 'Brand C', 'is_active': True}
            ]
        except:
            return []
    
    def get_monthly_summary(
        self,
        brand_id: Optional[str] = None,
        platform: Optional[str] = None,
        year: int = 2024,
        month: int = 1
    ) -> List[Dict[str, Any]]:
        """Get monthly summary data"""
        params = {'year': year, 'month': month}
        if brand_id:
            params['brand_id'] = brand_id
        if platform:
            params['platform'] = platform
        
        return self._make_request('GET', '/summary/monthly', params=params)
    
    def get_trends(
        self,
        brand_id: str,
        platform: Optional[str] = None,
        months: int = 6
    ) -> Dict[str, Any]:
        """Get trend data"""
        params = {'months': months}
        if platform:
            params['platform'] = platform
        
        return self._make_request('GET', f'/summary/trends?brand_id={brand_id}', params=params)
    
    def get_items(
        self,
        brand_id: Optional[str] = None,
        platform: Optional[str] = None,
        sentiment: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get social media items"""
        params = {'limit': limit, 'offset': offset}
        
        if brand_id:
            params['brand_id'] = brand_id
        if platform:
            params['platform'] = platform
        if sentiment:
            params['sentiment'] = sentiment
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return self._make_request('GET', '/items', params=params)
    
    def get_item_detail(self, item_id: str) -> Dict[str, Any]:
        """Get detailed item information"""
        return self._make_request('GET', f'/items/{item_id}')
    
    def get_items_stats(
        self,
        brand_id: Optional[str] = None,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get items statistics"""
        params = {}
        if brand_id:
            params['brand_id'] = brand_id
        if platform:
            params['platform'] = platform
        
        return self._make_request('GET', '/items/stats', params=params)
    
    def compare_brands(
        self,
        brand_ids: List[str],
        platform: Optional[str] = None,
        year: int = 2024,
        month: int = 1
    ) -> Dict[str, Any]:
        """Compare multiple brands"""
        params = {
            'brand_ids': brand_ids,
            'year': year,
            'month': month
        }
        if platform:
            params['platform'] = platform
        
        return self._make_request('GET', '/summary/comparison', params=params)
    
    def trigger_ingestion(
        self,
        platform: str,
        brand_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Trigger data ingestion"""
        endpoint = f'/ingest/{platform}'
        data = {'brand_id': brand_id, **kwargs}
        
        return self._make_request('POST', endpoint, json=data)
    
    def trigger_classification(
        self,
        brand_id: Optional[str] = None,
        platform: Optional[str] = None,
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """Trigger classification job"""
        data = {
            'brand_id': brand_id,
            'platform': platform,
            'force_reprocess': force_reprocess
        }
        
        return self._make_request('POST', '/classify/run', json=data)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        return self._make_request('GET', f'/ingest/status/{task_id}')
    
    def export_data(
        self,
        format: str = 'csv',
        brand_id: Optional[str] = None,
        platform: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_raw_data: bool = False
    ) -> requests.Response:
        """Export data (returns raw response for file download)"""
        params = {'format': format}
        
        if brand_id:
            params['brand_id'] = brand_id
        if platform:
            params['platform'] = platform
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if include_raw_data:
            params['include_raw_data'] = include_raw_data
        
        url = f"{self.api_v1}/export/{format}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_summary(api_client: APIClient, brand_id: str, year: int, month: int):
    """Cached version of monthly summary"""
    return api_client.get_monthly_summary(brand_id=brand_id, year=year, month=month)


@st.cache_data(ttl=300)
def get_cached_trends(api_client: APIClient, brand_id: str, months: int):
    """Cached version of trends data"""
    return api_client.get_trends(brand_id=brand_id, months=months)


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_cached_metrics(api_client: APIClient):
    """Cached version of system metrics"""
    return api_client.get_metrics()
