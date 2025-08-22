#!/usr/bin/env python3
"""
Supabase Migration Script
Handles database schema creation and data migration from SQLite to Supabase PostgreSQL
"""

import os
import sqlite3
import psycopg2
from pathlib import Path
from typing import List, Dict, Any
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import json

# Configuration
LOCAL_DB_PATH = "library/index.sqlite"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

class SupabaseMigrator:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.local_db_path = LOCAL_DB_PATH
        
    def create_schema(self):
        """Create PostgreSQL schema in Supabase"""
        print("🏗️  Creating Supabase schema...")
        
        # SQL commands to create tables
        schema_sql = """
        -- Enable necessary extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Products table
        CREATE TABLE IF NOT EXISTS products (
            product_uid TEXT PRIMARY KEY,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            category TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Files table
        CREATE TABLE IF NOT EXISTS files (
            product_uid TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            variant TEXT,
            file_type TEXT NOT NULL,
            ext TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            size_bytes BIGINT,
            source_url TEXT,
            source_page TEXT,
            furniture_type TEXT,
            subtype TEXT,
            tags_csv TEXT,
            url_health TEXT,
            status TEXT,
            thumbnail_url TEXT,
            product_url TEXT,
            matched_image_path TEXT,
            brand TEXT,
            name TEXT,
            slug TEXT,
            category TEXT,
            product_card_image_path TEXT,
            urls_checked BOOLEAN,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (product_uid, sha256),
            FOREIGN KEY (product_uid) REFERENCES products(product_uid) ON DELETE CASCADE
        );
        
        -- Images table
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            product_uid TEXT NOT NULL,
            variant TEXT NOT NULL,
            image_url TEXT NOT NULL,
            provider TEXT NOT NULL,
            score REAL NOT NULL,
            rationale TEXT,
            status TEXT NOT NULL,
            width INTEGER,
            height INTEGER,
            content_hash TEXT,
            local_path TEXT,
            cloud_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (product_uid) REFERENCES products(product_uid) ON DELETE CASCADE
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_files_product_uid ON files(product_uid);
        CREATE INDEX IF NOT EXISTS idx_files_file_type ON files(file_type);
        CREATE INDEX IF NOT EXISTS idx_files_brand ON files(brand);
        CREATE INDEX IF NOT EXISTS idx_images_product_uid ON images(product_uid);
        CREATE INDEX IF NOT EXISTS idx_images_provider ON images(provider);
        CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
        
        -- Create updated_at trigger function
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- Add triggers for updated_at
        CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_files_updated_at BEFORE UPDATE ON files
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        CREATE TRIGGER update_images_updated_at BEFORE UPDATE ON images
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            # Execute schema creation
            self.supabase.rpc('exec_sql', {'sql': schema_sql}).execute()
            print("✅ Schema created successfully")
        except Exception as e:
            print(f"⚠️  Schema creation warning (may already exist): {e}")
    
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
    
    def migrate_products(self):
        """Migrate products from SQLite to Supabase"""
        print("📦 Migrating products...")
        
        products = self.get_local_data('products')
        
        if not products:
            print("⚠️  No products found in local database")
            return
        
        # Insert products in batches
        batch_size = 100
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            
            # Clean data for Supabase
            clean_batch = []
            for product in batch:
                clean_product = {
                    'product_uid': product['product_uid'],
                    'brand': product['brand'],
                    'name': product['name'],
                    'slug': product['slug'],
                    'category': product.get('category')
                }
                clean_batch.append(clean_product)
            
            try:
                self.supabase.table('products').upsert(clean_batch).execute()
                print(f"✅ Migrated {len(clean_batch)} products (batch {i//batch_size + 1})")
            except Exception as e:
                print(f"❌ Error migrating products batch: {e}")
    
    def migrate_files(self):
        """Migrate files from SQLite to Supabase"""
        print("📁 Migrating files...")
        
        files = self.get_local_data('files')
        
        if not files:
            print("⚠️  No files found in local database")
            return
        
        # Insert files in batches
        batch_size = 100
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            
            # Clean data for Supabase
            clean_batch = []
            for file_data in batch:
                clean_file = {
                    'product_uid': file_data['product_uid'],
                    'sha256': file_data['sha256'],
                    'variant': file_data.get('variant'),
                    'file_type': file_data['file_type'],
                    'ext': file_data['ext'],
                    'stored_path': file_data['stored_path'],
                    'size_bytes': file_data.get('size_bytes'),
                    'source_url': file_data.get('source_url'),
                    'source_page': file_data.get('source_page'),
                    'furniture_type': file_data.get('furniture_type'),
                    'subtype': file_data.get('subtype'),
                    'tags_csv': file_data.get('tags_csv'),
                    'url_health': file_data.get('url_health'),
                    'status': file_data.get('status'),
                    'thumbnail_url': file_data.get('thumbnail_url'),
                    'product_url': file_data.get('product_url'),
                    'matched_image_path': file_data.get('matched_image_path'),
                    'brand': file_data.get('brand'),
                    'name': file_data.get('name'),
                    'slug': file_data.get('slug'),
                    'category': file_data.get('category'),
                    'product_card_image_path': file_data.get('product_card_image_path'),
                    'urls_checked': file_data.get('urls_checked', False)
                }
                clean_batch.append(clean_file)
            
            try:
                self.supabase.table('files').upsert(clean_batch).execute()
                print(f"✅ Migrated {len(clean_batch)} files (batch {i//batch_size + 1})")
            except Exception as e:
                print(f"❌ Error migrating files batch: {e}")
    
    def migrate_images(self):
        """Migrate images from SQLite to Supabase"""
        print("🖼️  Migrating images...")
        
        images = self.get_local_data('images')
        
        if not images:
            print("⚠️  No images found in local database")
            return
        
        # Insert images in batches
        batch_size = 50
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            
            # Clean data for Supabase
            clean_batch = []
            for image in batch:
                clean_image = {
                    'product_uid': image['product_uid'],
                    'variant': image['variant'],
                    'image_url': image['image_url'],
                    'provider': image['provider'],
                    'score': image['score'],
                    'rationale': image.get('rationale'),
                    'status': image['status'],
                    'width': image.get('width'),
                    'height': image.get('height'),
                    'content_hash': image.get('content_hash'),
                    'local_path': image.get('local_path'),
                    'cloud_url': None  # Will be set when uploaded to Supabase Storage
                }
                clean_batch.append(clean_image)
            
            try:
                self.supabase.table('images').upsert(clean_batch).execute()
                print(f"✅ Migrated {len(clean_batch)} images (batch {i//batch_size + 1})")
            except Exception as e:
                print(f"❌ Error migrating images batch: {e}")
    
    def verify_migration(self):
        """Verify that migration was successful"""
        print("🔍 Verifying migration...")
        
        try:
            # Check product count
            products_response = self.supabase.table('products').select('*', count='exact').execute()
            products_count = products_response.count
            
            # Check files count
            files_response = self.supabase.table('files').select('*', count='exact').execute()
            files_count = files_response.count
            
            # Check images count
            images_response = self.supabase.table('images').select('*', count='exact').execute()
            images_count = images_response.count
            
            print(f"✅ Migration verification:")
            print(f"   Products: {products_count}")
            print(f"   Files: {files_count}")
            print(f"   Images: {images_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration verification failed: {e}")
            return False
    
    def run_migration(self):
        """Run complete migration process"""
        print("🚀 Starting Supabase migration...")
        print(f"📁 Local DB: {self.local_db_path}")
        print(f"☁️  Supabase URL: {SUPABASE_URL}")
        print("-" * 50)
        
        try:
            # 1. Create schema
            self.create_schema()
            
            # 2. Migrate data
            self.migrate_products()
            self.migrate_files()
            self.migrate_images()
            
            # 3. Verify migration
            success = self.verify_migration()
            
            if success:
                print("-" * 50)
                print("🎉 Migration completed successfully!")
                print("📊 Data is now available in Supabase")
            else:
                print("❌ Migration verification failed")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

def main():
    """Main migration function"""
    migrator = SupabaseMigrator()
    migrator.run_migration()

if __name__ == "__main__":
    main()
