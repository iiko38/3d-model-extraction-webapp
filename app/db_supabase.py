"""
Supabase Database Layer
Replaces SQLite with Supabase PostgreSQL for cloud deployment
"""

import os
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
from .settings_cloud import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseDB:
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("Supabase configuration not found")
        
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
    
    def get_products(self, 
                    search: Optional[str] = None,
                    brand: Optional[str] = None,
                    page: int = 1,
                    per_page: int = 20) -> Dict[str, Any]:
        """Get products with filtering and pagination"""
        try:
            query = self.supabase.table('products').select('*')
            
            # Apply filters
            if brand:
                query = query.eq('brand', brand)
            
            if search:
                query = query.or_(f'name.ilike.%{search}%,slug.ilike.%{search}%')
            
            # Get total count
            count_query = query
            count_response = count_query.execute()
            total_count = len(count_response.data)
            
            # Apply pagination
            offset = (page - 1) * per_page
            query = query.range(offset, offset + per_page - 1)
            
            # Execute query
            response = query.execute()
            
            return {
                'products': response.data,
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'pages': (total_count + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return {
                'products': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'pages': 0
            }
    
    def get_product_detail(self, product_uid: str) -> Optional[Dict[str, Any]]:
        """Get detailed product information"""
        try:
            response = self.supabase.table('products').select('*').eq('product_uid', product_uid).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting product detail: {e}")
            return None
    
    def get_product_files(self, product_uid: str) -> List[Dict[str, Any]]:
        """Get files for a specific product"""
        try:
            response = self.supabase.table('files').select('*').eq('product_uid', product_uid).execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting product files: {e}")
            return []
    
    def get_product_images(self, product_uid: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get images for a specific product"""
        try:
            query = self.supabase.table('images').select('*').eq('product_uid', product_uid)
            
            if status:
                query = query.eq('status', status)
            
            response = query.execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting product images: {e}")
            return []
    
    def get_files_with_filters(self,
                              search: Optional[str] = None,
                              brand: Optional[str] = None,
                              file_type: Optional[str] = None,
                              furniture_type: Optional[str] = None,
                              status: Optional[str] = None,
                              url_health: Optional[str] = None,
                              page: int = 1,
                              per_page: int = 50) -> Dict[str, Any]:
        """Get files with advanced filtering"""
        try:
            query = self.supabase.table('files').select('*')
            
            # Apply filters
            if brand:
                query = query.eq('brand', brand)
            
            if file_type:
                query = query.eq('file_type', file_type)
            
            if furniture_type:
                query = query.eq('furniture_type', furniture_type)
            
            if status:
                query = query.eq('status', status)
            
            if url_health:
                query = query.eq('url_health', url_health)
            
            if search:
                query = query.or_(f'name.ilike.%{search}%,product_uid.ilike.%{search}%')
            
            # Get total count
            count_response = query.execute()
            total_count = len(count_response.data)
            
            # Apply pagination
            offset = (page - 1) * per_page
            query = query.range(offset, offset + per_page - 1)
            
            # Execute query
            response = query.execute()
            
            return {
                'files': response.data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting files with filters: {e}")
            return {
                'files': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0
                }
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        try:
            stats = {}
            
            # Product counts by brand
            products_response = self.supabase.table('products').select('brand').execute()
            brand_counts = {}
            for product in products_response.data:
                brand = product['brand']
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            stats['brand_stats'] = brand_counts
            
            # File type distribution
            files_response = self.supabase.table('files').select('file_type,size_bytes').execute()
            file_type_counts = {}
            total_size = 0
            for file_data in files_response.data:
                file_type = file_data['file_type']
                file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
                if file_data.get('size_bytes'):
                    total_size += file_data['size_bytes']
            stats['file_type_stats'] = file_type_counts
            stats['total_size'] = total_size
            
            # Image statistics
            images_response = self.supabase.table('images').select('provider,status').execute()
            image_stats = {}
            for image in images_response.data:
                provider = image['provider']
                status = image['status']
                key = f"{provider}_{status}"
                image_stats[key] = image_stats.get(key, 0) + 1
            stats['image_stats'] = image_stats
            
            # Overall counts
            stats['total_products'] = len(products_response.data)
            stats['total_files'] = len(files_response.data)
            stats['total_images'] = len(images_response.data)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'total_products': 0,
                'total_files': 0,
                'total_images': 0,
                'brand_stats': {},
                'file_type_stats': {},
                'image_stats': {},
                'total_size': 0
            }
    
    def get_unique_values(self, column: str, table: str = 'files') -> List[str]:
        """Get unique values for a column (for filter options)"""
        try:
            response = self.supabase.table(table).select(column).execute()
            values = set()
            for row in response.data:
                if row.get(column):
                    values.add(row[column])
            return sorted(list(values))
            
        except Exception as e:
            logger.error(f"Error getting unique values: {e}")
            return []
    
    def get_file_by_sha256(self, sha256: str) -> Optional[Dict[str, Any]]:
        """Get file by SHA256 hash"""
        try:
            response = self.supabase.table('files').select('*').eq('sha256', sha256).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting file by SHA256: {e}")
            return None

# Global database instance
db = SupabaseDB()
