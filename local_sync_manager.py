#!/usr/bin/env python3
"""
Local Sync Manager
Keeps Supabase database updated with new data from local scrapes
"""

import os
import sqlite3
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
LOCAL_DB_PATH = "library/index.sqlite"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

class LocalSyncManager:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.local_db_path = LOCAL_DB_PATH
        
    def get_local_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Get data from local SQLite database"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append(dict(row))
        
        conn.close()
        return data
    
    def get_supabase_data(self, table_name: str, key_field: str = None) -> Dict[str, Any]:
        """Get existing data from Supabase for comparison"""
        try:
            response = self.supabase.table(table_name).select('*').execute()
            
            if key_field:
                # Create a dictionary with key_field as key
                return {row[key_field]: row for row in response.data}
            else:
                return {row['id']: row for row in response.data}
                
        except Exception as e:
            logger.error(f"Error getting Supabase data from {table_name}: {e}")
            return {}
    
    async def sync_products(self):
        """Sync new products from local SQLite to Supabase"""
        logger.info("🔄 Syncing products...")
        
        local_products = self.get_local_data('products')
        supabase_products = self.get_supabase_data('products', 'product_uid')
        
        new_products = []
        updated_products = []
        
        for local_product in local_products:
            product_uid = local_product['product_uid']
            
            if product_uid not in supabase_products:
                # New product
                new_products.append({
                    'product_uid': product_uid,
                    'brand': local_product['brand'],
                    'name': local_product['name'],
                    'slug': local_product['slug'],
                    'category': local_product.get('category')
                })
            else:
                # Check if update is needed
                supabase_product = supabase_products[product_uid]
                if (supabase_product['name'] != local_product['name'] or
                    supabase_product['brand'] != local_product['brand'] or
                    supabase_product['slug'] != local_product['slug']):
                    
                    updated_products.append({
                        'product_uid': product_uid,
                        'brand': local_product['brand'],
                        'name': local_product['name'],
                        'slug': local_product['slug'],
                        'category': local_product.get('category')
                    })
        
        # Insert new products
        if new_products:
            try:
                self.supabase.table('products').upsert(new_products).execute()
                logger.info(f"✅ Added {len(new_products)} new products")
            except Exception as e:
                logger.error(f"❌ Error adding new products: {e}")
        
        # Update existing products
        if updated_products:
            try:
                self.supabase.table('products').upsert(updated_products).execute()
                logger.info(f"✅ Updated {len(updated_products)} products")
            except Exception as e:
                logger.error(f"❌ Error updating products: {e}")
        
        if not new_products and not updated_products:
            logger.info("✅ Products are up to date")
    
    async def sync_files(self):
        """Sync new files from local SQLite to Supabase"""
        logger.info("🔄 Syncing files...")
        
        local_files = self.get_local_data('files')
        supabase_files = self.get_supabase_data('files', 'sha256')
        
        new_files = []
        updated_files = []
        
        for local_file in local_files:
            sha256 = local_file['sha256']
            composite_key = f"{local_file['product_uid']}_{sha256}"
            
            if composite_key not in supabase_files:
                # New file
                new_files.append({
                    'product_uid': local_file['product_uid'],
                    'sha256': sha256,
                    'variant': local_file.get('variant'),
                    'file_type': local_file['file_type'],
                    'ext': local_file['ext'],
                    'stored_path': local_file['stored_path'],
                    'size_bytes': local_file.get('size_bytes'),
                    'source_url': local_file.get('source_url'),
                    'source_page': local_file.get('source_page'),
                    'furniture_type': local_file.get('furniture_type'),
                    'subtype': local_file.get('subtype'),
                    'tags_csv': local_file.get('tags_csv'),
                    'url_health': local_file.get('url_health'),
                    'status': local_file.get('status'),
                    'thumbnail_url': local_file.get('thumbnail_url'),
                    'product_url': local_file.get('product_url'),
                    'matched_image_path': local_file.get('matched_image_path'),
                    'brand': local_file.get('brand'),
                    'name': local_file.get('name'),
                    'slug': local_file.get('slug'),
                    'category': local_file.get('category'),
                    'product_card_image_path': local_file.get('product_card_image_path'),
                    'urls_checked': local_file.get('urls_checked', False)
                })
        
        # Insert new files in batches
        batch_size = 100
        for i in range(0, len(new_files), batch_size):
            batch = new_files[i:i + batch_size]
            try:
                self.supabase.table('files').upsert(batch).execute()
                logger.info(f"✅ Added batch {i//batch_size + 1} of files ({len(batch)} files)")
            except Exception as e:
                logger.error(f"❌ Error adding files batch: {e}")
        
        if not new_files:
            logger.info("✅ Files are up to date")
    
    async def sync_images(self):
        """Sync new images from local SQLite to Supabase"""
        logger.info("🔄 Syncing images...")
        
        local_images = self.get_local_data('images')
        supabase_images = self.get_supabase_data('images', 'id')
        
        new_images = []
        
        for local_image in local_images:
            # Check if image already exists by content_hash or image_url
            existing = False
            for supabase_image in supabase_images.values():
                if (supabase_image.get('content_hash') == local_image.get('content_hash') or
                    supabase_image.get('image_url') == local_image.get('image_url')):
                    existing = True
                    break
            
            if not existing:
                new_images.append({
                    'product_uid': local_image['product_uid'],
                    'variant': local_image['variant'],
                    'image_url': local_image['image_url'],
                    'provider': local_image['provider'],
                    'score': local_image['score'],
                    'rationale': local_image.get('rationale'),
                    'status': local_image['status'],
                    'width': local_image.get('width'),
                    'height': local_image.get('height'),
                    'content_hash': local_image.get('content_hash'),
                    'local_path': local_image.get('local_path'),
                    'cloud_url': None  # Will be set when uploaded to Supabase Storage
                })
        
        # Insert new images in batches
        batch_size = 50
        for i in range(0, len(new_images), batch_size):
            batch = new_images[i:i + batch_size]
            try:
                self.supabase.table('images').upsert(batch).execute()
                logger.info(f"✅ Added batch {i//batch_size + 1} of images ({len(batch)} images)")
            except Exception as e:
                logger.error(f"❌ Error adding images batch: {e}")
        
        if not new_images:
            logger.info("✅ Images are up to date")
    
    async def upload_images_to_cloud(self):
        """Upload local images to Supabase Storage"""
        logger.info("☁️  Uploading images to cloud storage...")
        
        # Get images that don't have cloud_url set
        response = self.supabase.table('images').select('*').is_('cloud_url', 'null').execute()
        images_to_upload = response.data
        
        for image in images_to_upload:
            local_path = image.get('local_path')
            if not local_path:
                continue
            
            file_path = Path(local_path)
            if not file_path.exists():
                logger.warning(f"⚠️  Local image not found: {local_path}")
                continue
            
            try:
                # Upload to Supabase Storage
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                # Generate cloud path
                cloud_path = f"images/{image['product_uid']}/{file_path.name}"
                
                # Upload to Supabase Storage
                storage_response = self.supabase.storage.from_(settings.CLOUD_STORAGE_BUCKET).upload(
                    cloud_path,
                    file_data,
                    {"content-type": "image/jpeg"}
                )
                
                # Get public URL
                cloud_url = self.supabase.storage.from_(settings.CLOUD_STORAGE_BUCKET).get_public_url(cloud_path)
                
                # Update database with cloud URL
                self.supabase.table('images').update({
                    'cloud_url': cloud_url
                }).eq('id', image['id']).execute()
                
                logger.info(f"✅ Uploaded image: {cloud_path}")
                
            except Exception as e:
                logger.error(f"❌ Error uploading image {local_path}: {e}")
    
    async def run_full_sync(self):
        """Run complete sync process"""
        logger.info("🚀 Starting full sync process...")
        
        try:
            await self.sync_products()
            await self.sync_files()
            await self.sync_images()
            await self.upload_images_to_cloud()
            
            logger.info("🎉 Full sync completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Full sync failed: {e}")
            raise
    
    async def run_incremental_sync(self):
        """Run incremental sync (only new data)"""
        logger.info("🔄 Starting incremental sync...")
        
        try:
            await self.sync_products()
            await self.sync_files()
            await self.sync_images()
            
            logger.info("✅ Incremental sync completed!")
            
        except Exception as e:
            logger.error(f"❌ Incremental sync failed: {e}")
            raise
    
    def check_for_changes(self) -> bool:
        """Check if there are any changes in local database"""
        # Simple check - compare file modification times
        local_db_path = Path(self.local_db_path)
        if not local_db_path.exists():
            return False
        
        # Check if database was modified recently (within last hour)
        db_mtime = local_db_path.stat().st_mtime
        current_time = datetime.now().timestamp()
        
        return (current_time - db_mtime) < 3600  # 1 hour

def main():
    """Main sync function"""
    import asyncio
    
    try:
        sync_manager = LocalSyncManager()
        asyncio.run(sync_manager.run_full_sync())
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        raise

if __name__ == "__main__":
    main()
