"""
Refactored Database Layer for 3D Warehouse
Supports new schema with FTS5 search, enhanced files table, and bulk operations
"""

import sqlite3
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "library/index.sqlite"):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure database file exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def run_query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute a query and return results as list of dicts."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []
    
    def execute_update(self, sql: str, params: tuple = ()) -> bool:
        """Execute an update/insert/delete query."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Update error: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def get_files_with_filters(self, 
                              search: Optional[str] = None,
                              brand: Optional[str] = None,
                              file_type: Optional[str] = None,
                              furniture_type: Optional[str] = None,
                              status: Optional[str] = None,
                              url_health: Optional[str] = None,
                              page: int = 1,
                              per_page: int = 50) -> Dict[str, Any]:
        """Get files with advanced filtering and FTS5 search."""
        
        # Build WHERE clause
        where_conditions = []
        params = {}
        
        if search:
            # Use FTS5 search
            where_conditions.append("""
                f.sha256 IN (
                    SELECT sha256 FROM files_fts 
                    WHERE files_fts MATCH ?
                )
            """)
            params['search'] = search
        
        if brand:
            where_conditions.append("p.brand = :brand")
            params['brand'] = brand
        
        if file_type:
            where_conditions.append("f.file_type = :file_type")
            params['file_type'] = file_type
        
        if furniture_type:
            where_conditions.append("f.furniture_type = :furniture_type")
            params['furniture_type'] = furniture_type
        
        if status:
            where_conditions.append("f.status = :status")
            params['status'] = status
        
        if url_health:
            where_conditions.append("f.url_health = :url_health")
            params['url_health'] = url_health
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Count query
        count_sql = f"""
            SELECT COUNT(*) as total
            FROM files f
            LEFT JOIN products p ON f.product_uid = p.product_uid
            WHERE {where_clause}
        """
        
        # Main query
        offset = (page - 1) * per_page
        main_sql = f"""
            SELECT 
                f.*,
                p.brand,
                p.name as product_name,
                p.slug as product_slug,
                p.category
            FROM files f
            LEFT JOIN products p ON f.product_uid = p.product_uid
            WHERE {where_clause}
            ORDER BY f.sha256 DESC
            LIMIT :limit OFFSET :offset
        """
        
        params.update({
            'limit': per_page,
            'offset': offset
        })
        
        # Execute queries
        total_result = self.run_query(count_sql, {k: v for k, v in params.items() if k not in ['limit', 'offset']})
        files = self.run_query(main_sql, params)
        
        total = total_result[0]['total'] if total_result else 0
        total_pages = max(1, (total + per_page - 1) // per_page)
        
        return {
            'files': files,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'start_item': offset + 1,
                'end_item': min(offset + per_page, total)
            }
        }
    
    def get_file_by_sha256(self, sha256: str) -> Optional[Dict]:
        """Get a single file by SHA256."""
        sql = """
            SELECT 
                f.*,
                p.brand,
                p.name as product_name,
                p.slug as product_slug,
                p.category
            FROM files f
            LEFT JOIN products p ON f.product_uid = p.product_uid
            WHERE f.sha256 = ?
        """
        results = self.run_query(sql, (sha256,))
        return results[0] if results else None
    
    def update_file_field(self, sha256: str, field: str, value: str) -> bool:
        """Update a single field for a file."""
        sql = f"UPDATE files SET {field} = ? WHERE sha256 = ?"
        return self.execute_update(sql, (value, sha256))
    
    def bulk_update_files(self, sha256s: List[str], updates: Dict[str, str]) -> bool:
        """Bulk update multiple files with the same values."""
        if not updates or not sha256s:
            return False
        
        # Deduplicate sha256s to prevent unique constraint violations
        unique_sha256s = list(set(sha256s))
        if len(unique_sha256s) != len(sha256s):
            print(f"Warning: Removed {len(sha256s) - len(unique_sha256s)} duplicate sha256s")
        
        if not unique_sha256s:
            return False
        
        # Filter out primary key fields to prevent unique constraint violations
        safe_updates = {k: v for k, v in updates.items() if k not in ['product_uid', 'sha256']}
        if not safe_updates:
            print("Warning: No safe fields to update (excluding primary keys)")
            return False
        
        # Retry mechanism for database locks
        max_retries = 3
        for attempt in range(max_retries):
            try:
                set_clause = ", ".join([f"{field} = ?" for field in safe_updates.keys()])
                
                placeholders = ", ".join(["?" for _ in unique_sha256s])
                sql = f"UPDATE files SET {set_clause} WHERE sha256 IN ({placeholders})"
                
                params = list(safe_updates.values()) + unique_sha256s
                success = self.execute_update(sql, tuple(params))
                
                # Auto-update url_health if URLs were changed
                if success and ('thumbnail_url' in safe_updates or 'product_url' in safe_updates):
                    self._update_url_health_for_files(unique_sha256s)
                
                return success
            except Exception as e:
                print(f"Update error (attempt {attempt + 1}/{max_retries}): {e}")
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    import time
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                return False

    def _update_url_health_for_files(self, sha256s: List[str]):
        """Update url_health for files based on their URLs."""
        try:
            # Set url_health to 'checking' for files with URLs
            placeholders = ", ".join(["?" for _ in sha256s])
            sql = """
                UPDATE files 
                SET url_health = CASE 
                    WHEN thumbnail_url IS NOT NULL OR product_url IS NOT NULL THEN 'checking'
                    ELSE 'unknown'
                END
                WHERE sha256 IN ({})
            """.format(placeholders)
            
            self.execute_update(sql, tuple(sha256s))
        except Exception as e:
            print(f"Error updating url_health: {e}")
    
    def get_unique_values(self, field: str, table: str = "files") -> List[str]:
        """Get unique values for a field."""
        sql = f"SELECT DISTINCT {field} FROM {table} WHERE {field} IS NOT NULL ORDER BY {field}"
        results = self.run_query(sql)
        return [row[field] for row in results]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        stats = {}
        
        # File counts by type
        file_types = self.run_query("""
            SELECT file_type, COUNT(*) as count 
            FROM files 
            GROUP BY file_type 
            ORDER BY count DESC
        """)
        stats['file_types'] = file_types
        
        # Furniture types
        furniture_types = self.run_query("""
            SELECT furniture_type, COUNT(*) as count 
            FROM files 
            WHERE furniture_type IS NOT NULL
            GROUP BY furniture_type 
            ORDER BY count DESC
        """)
        stats['furniture_types'] = furniture_types
        
        # URL health
        url_health = self.run_query("""
            SELECT url_health, COUNT(*) as count 
            FROM files 
            GROUP BY url_health 
            ORDER BY count DESC
        """)
        stats['url_health'] = url_health
        
        # Status
        status = self.run_query("""
            SELECT status, COUNT(*) as count 
            FROM files 
            GROUP BY status 
            ORDER BY count DESC
        """)
        stats['status'] = status
        
        # Brands
        brands = self.run_query("""
            SELECT p.brand, COUNT(*) as count 
            FROM files f
            LEFT JOIN products p ON f.product_uid = p.product_uid
            GROUP BY p.brand 
            ORDER BY count DESC
        """)
        stats['brands'] = brands
        
        # Totals
        totals = self.run_query("""
            SELECT 
                COUNT(*) as total_files,
                COUNT(DISTINCT product_uid) as total_products,
                SUM(size_bytes) as total_size
            FROM files
        """)
        stats['totals'] = totals[0] if totals else {}
        
        return stats
    
    def get_bundle_files(self, product_uid: str, preferred_formats: List[str] = None) -> List[Dict]:
        """Get files for a product bundle, prioritizing preferred formats."""
        if not preferred_formats:
            preferred_formats = ['revit', 'sketchup', 'autocad_3d', 'obj', 'fbx']
        
        # Build ORDER BY clause for format preference
        order_cases = []
        for i, fmt in enumerate(preferred_formats):
            order_cases.append(f"WHEN f.file_type = '{fmt}' THEN {i}")
        
        order_clause = f"CASE {' '.join(order_cases)} ELSE {len(preferred_formats)} END"
        
        sql = f"""
            SELECT 
                f.*,
                p.brand,
                p.name as product_name
            FROM files f
            LEFT JOIN products p ON f.product_uid = p.product_uid
            WHERE f.product_uid = ? AND f.status = 'active'
            ORDER BY {order_clause}, f.file_type
        """
        
        return self.run_query(sql, (product_uid,))
    
    def search_files(self, query: str, limit: int = 50) -> List[Dict]:
        """Search files using FTS5."""
        sql = """
            SELECT 
                f.*,
                p.brand,
                p.name as product_name,
                p.slug as product_slug
            FROM files f
            LEFT JOIN products p ON f.product_uid = p.product_uid
            WHERE f.sha256 IN (
                SELECT sha256 FROM files_fts 
                WHERE files_fts MATCH ?
            )
            ORDER BY f.sha256 DESC
            LIMIT ?
        """
        return self.run_query(sql, (query, limit))
    
    def get_products_with_file_counts(self) -> List[Dict]:
        """Get products with their file counts."""
        sql = """
            SELECT 
                p.*,
                COUNT(f.sha256) as file_count,
                COUNT(CASE WHEN f.status = 'active' THEN 1 END) as active_files
            FROM products p
            LEFT JOIN files f ON p.product_uid = f.product_uid
            GROUP BY p.product_uid
            ORDER BY file_count DESC
        """
        return self.run_query(sql)

    def get_variants_with_filters(self, search=None, brand=None, furniture_type=None, 
                                status=None, url_health=None, urls_checked=None, page=1, per_page=50):
        """Get variants grouped by product_uid and variant with filters."""
        
        # Build WHERE clause
        conditions = []
        params = {}
        
        if search:
            conditions.append("(f.variant LIKE :search OR p.name LIKE :search OR p.brand LIKE :search)")
            params['search'] = f"%{search}%"
        
        if brand:
            conditions.append("p.brand = :brand")
            params['brand'] = brand
        
        if furniture_type:
            conditions.append("f.furniture_type = :furniture_type")
            params['furniture_type'] = furniture_type
        
        if status:
            conditions.append("f.status = :status")
            params['status'] = status
        
        if url_health:
            conditions.append("f.url_health = :url_health")
            params['url_health'] = url_health
        
        if urls_checked is not None:
            if urls_checked == '1':
                conditions.append("f.urls_checked = 1")
            elif urls_checked == '0':
                conditions.append("(f.urls_checked = 0 OR f.urls_checked IS NULL)")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get total count
        count_sql = f"""
            SELECT COUNT(DISTINCT f.product_uid || '|' || f.variant) as total
            FROM files f
            LEFT JOIN products p ON f.product_uid = p.product_uid
            WHERE {where_clause}
        """
        total_result = self.run_query(count_sql, params)
        total_variants = total_result[0]['total'] if total_result else 0
        
        # Calculate pagination
        offset = (page - 1) * per_page
        total_pages = (total_variants + per_page - 1) // per_page
        
        # Get variants
        main_sql = f"""
            SELECT 
                f.product_uid,
                f.variant,
                f.furniture_type,
                f.subtype,
                f.tags_csv,
                f.status,
                f.url_health,
                f.urls_checked,
                f.thumbnail_url,
                f.product_url,
                f.matched_image_path,
                p.brand,
                p.name,
                p.slug,
                p.category,
                COUNT(f.sha256) as file_count
            FROM files f
            LEFT JOIN products p ON f.product_uid = p.product_uid
            WHERE {where_clause}
            GROUP BY f.product_uid, f.variant
            ORDER BY p.brand, p.name, f.variant
            LIMIT :limit OFFSET :offset
        """
        
        params['limit'] = per_page
        params['offset'] = offset
        
        variants = self.run_query(main_sql, params)
        
        # Get files for each variant
        for variant in variants:
            files_sql = """
                SELECT sha256, file_type, ext, size_bytes, stored_path
                FROM files 
                WHERE product_uid = :product_uid AND variant = :variant
                ORDER BY file_type, ext
            """
            variant['files'] = self.run_query(files_sql, {
                'product_uid': variant['product_uid'],
                'variant': variant['variant']
            })
        
        return {
            'variants': variants,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_variants': total_variants,
                'total_pages': total_pages
            }
        }

    def get_variant_data(self, product_uid, variant):
        """Get detailed data for a specific variant."""
        sql = """
            SELECT 
                f.product_uid,
                f.variant,
                f.furniture_type,
                f.subtype,
                f.tags_csv,
                f.status,
                f.url_health,
                f.urls_checked,
                f.thumbnail_url,
                f.product_url,
                f.source_url,
                f.source_page,
                f.matched_image_path,
                f.product_card_image_path,
                p.brand,
                p.name,
                p.slug,
                p.category
            FROM files f
            LEFT JOIN products p ON f.product_uid = p.product_uid
            WHERE f.product_uid = :product_uid AND f.variant = :variant
            LIMIT 1
        """
        
        result = self.run_query(sql, {'product_uid': product_uid, 'variant': variant})
        if not result:
            return None
        
        variant_data = result[0]
        
        # Get all files for this variant
        files_sql = """
            SELECT sha256, file_type, ext, size_bytes, stored_path
            FROM files 
            WHERE product_uid = :product_uid AND variant = :variant
            ORDER BY file_type, ext
        """
        variant_data['files'] = self.run_query(files_sql, {
            'product_uid': product_uid,
            'variant': variant
        })
        
        return variant_data

# Global database manager instance
db = DatabaseManager()
