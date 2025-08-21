"""
Thumbnail Download and Caching Service
Downloads and caches thumbnail images from URLs for checked files
"""

import os
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict, List
import sqlite3
import logging
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)

class ThumbnailService:
    def __init__(self, cache_dir: str = "static/thumbnails", db_path: str = "library/index.sqlite"):
        self.cache_dir = Path(cache_dir)
        self.db_path = db_path
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for better organization
        (self.cache_dir / "original").mkdir(exist_ok=True)
        (self.cache_dir / "processed").mkdir(exist_ok=True)
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': '3D-Warehouse-Thumbnail-Service/1.0'
        })
    
    def get_thumbnail_path(self, sha256: str, url: str) -> Path:
        """Generate a consistent file path for a thumbnail."""
        # Use SHA256 of the URL to avoid filename conflicts
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        ext = self._get_extension_from_url(url)
        return self.cache_dir / "original" / f"{sha256}_{url_hash[:8]}{ext}"
    
    def _get_extension_from_url(self, url: str) -> str:
        """Extract file extension from URL."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if path.endswith('.jpg') or path.endswith('.jpeg'):
            return '.jpg'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.webp'):
            return '.webp'
        elif path.endswith('.gif'):
            return '.gif'
        else:
            return '.jpg'  # Default to jpg
    
    def download_thumbnail(self, sha256: str, url: str, force: bool = False) -> Optional[str]:
        """Download and cache a thumbnail image."""
        if not url or not url.strip():
            return None
        
        file_path = self.get_thumbnail_path(sha256, url)
        
        # Check if already cached and not forcing re-download
        if file_path.exists() and not force:
            return str(file_path.relative_to("static"))
        
        try:
            logger.info(f"Downloading thumbnail for {sha256[:8]}... from {url}")
            
            response = self.session.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"URL {url} returned non-image content type: {content_type}")
                return None
            
            # Save the image
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded thumbnail: {file_path}")
            return str(file_path.relative_to("static")).replace("\\", "/")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download thumbnail from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading thumbnail: {e}")
            return None
    
    def get_files_needing_thumbnails(self) -> List[Dict]:
        """Get files that need thumbnail downloads (checked URLs with thumbnail URLs)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sha256, variant, thumbnail_url, product_uid
            FROM files 
            WHERE urls_checked = 1 
            AND thumbnail_url IS NOT NULL 
            AND thumbnail_url != ''
            ORDER BY product_uid, variant
        """)
        
        files = []
        for row in cursor.fetchall():
            files.append({
                'sha256': row[0],
                'variant': row[1],
                'thumbnail_url': row[2],
                'product_uid': row[3]
            })
        
        conn.close()
        return files
    
    def download_all_thumbnails(self, max_workers: int = 5) -> Dict[str, int]:
        """Download thumbnails for all files that need them."""
        files = self.get_files_needing_thumbnails()
        
        if not files:
            return {'total': 0, 'downloaded': 0, 'failed': 0}
        
        logger.info(f"Starting thumbnail download for {len(files)} files")
        
        downloaded = 0
        failed = 0
        
        for i, file_data in enumerate(files):
            try:
                result = self.download_thumbnail(
                    file_data['sha256'], 
                    file_data['thumbnail_url']
                )
                
                if result:
                    downloaded += 1
                    # Update database with local path
                    self._update_thumbnail_path(file_data['sha256'], result)
                else:
                    failed += 1
                
                # Progress logging
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{len(files)} files processed")
                
                # Small delay to be respectful to the server
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing file {file_data['sha256']}: {e}")
                failed += 1
        
        logger.info(f"Thumbnail download complete: {downloaded} downloaded, {failed} failed")
        return {
            'total': len(files),
            'downloaded': downloaded,
            'failed': failed
        }
    
    def _update_thumbnail_path(self, sha256: str, local_path: str):
        """Update the database with the local thumbnail path."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE files 
                SET matched_image_path = ?
                WHERE sha256 = ?
            """, (local_path, sha256))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to update thumbnail path for {sha256}: {e}")
        finally:
            conn.close()
    
    def get_thumbnail_url(self, sha256: str, thumbnail_url: str = None) -> Optional[str]:
        """Get the local URL for a thumbnail, downloading if necessary."""
        if not thumbnail_url:
            # Get from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT thumbnail_url FROM files WHERE sha256 = ?", (sha256,))
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:
                return None
            thumbnail_url = result[0]
        
        # Check if already cached
        file_path = self.get_thumbnail_path(sha256, thumbnail_url)
        if file_path.exists():
            return f"/static/thumbnails/original/{file_path.name}"
        
        # Try to download
        local_path = self.download_thumbnail(sha256, thumbnail_url)
        if local_path:
            return f"/{local_path}"
        
        return None
    
    def cleanup_orphaned_thumbnails(self):
        """Remove thumbnail files that no longer have corresponding database entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all SHA256s from database
        cursor.execute("SELECT sha256 FROM files")
        db_sha256s = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        # Check cache directory
        original_dir = self.cache_dir / "original"
        removed_count = 0
        
        for file_path in original_dir.glob("*.jpg"):
            # Extract SHA256 from filename (format: sha256_hash.ext)
            filename = file_path.stem
            sha256 = filename.split('_')[0]
            
            if sha256 not in db_sha256s:
                try:
                    file_path.unlink()
                    removed_count += 1
                    logger.info(f"Removed orphaned thumbnail: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove orphaned thumbnail {file_path}: {e}")
        
        logger.info(f"Cleanup complete: removed {removed_count} orphaned thumbnails")
        return removed_count

# Global instance
thumbnail_service = ThumbnailService()
