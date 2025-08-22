#!/usr/bin/env python3
"""
Create Supabase Schema
Creates the database tables in Supabase using direct SQL execution
"""

import os
from supabase import create_client, Client

# Configuration
SUPABASE_URL = "https://jcmnuxlusnfhusbulhag.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjbW51eGx1c25maHVzYnVsaGFnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTg2NjQ0NCwiZXhwIjoyMDcxNDQyNDQ0fQ.n0nnrYdxV2MUiPkyv2YPAI0hRhZLamsuGdo1wLii-Qs"

def create_schema():
    """Create the database schema in Supabase"""
    print("🏗️  Creating Supabase schema...")
    
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # SQL commands to create tables
    schema_commands = [
        # Products table
        """
        CREATE TABLE IF NOT EXISTS products (
            product_uid TEXT PRIMARY KEY,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            category TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        # Files table
        """
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
            urls_checked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (product_uid, sha256)
        );
        """,
        
        # Images table
        """
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
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        # Create indexes
        """
        CREATE INDEX IF NOT EXISTS idx_files_product_uid ON files(product_uid);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_files_file_type ON files(file_type);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_files_brand ON files(brand);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_images_product_uid ON images(product_uid);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_images_provider ON images(provider);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
        """
    ]
    
    try:
        # Execute each SQL command
        for i, sql in enumerate(schema_commands):
            print(f"Executing command {i+1}/{len(schema_commands)}...")
            result = supabase.rpc('exec_sql', {'sql': sql}).execute()
            print(f"✅ Command {i+1} executed successfully")
            
    except Exception as e:
        print(f"⚠️  Schema creation warning: {e}")
        print("Tables may already exist or there might be permission issues.")
        
        # Try to check if tables exist
        try:
            # Test if products table exists
            result = supabase.table('products').select('product_uid').limit(1).execute()
            print("✅ Products table exists")
        except Exception as e2:
            print(f"❌ Products table does not exist: {e2}")
            
        try:
            # Test if files table exists
            result = supabase.table('files').select('product_uid').limit(1).execute()
            print("✅ Files table exists")
        except Exception as e2:
            print(f"❌ Files table does not exist: {e2}")
            
        try:
            # Test if images table exists
            result = supabase.table('images').select('id').limit(1).execute()
            print("✅ Images table exists")
        except Exception as e2:
            print(f"❌ Images table does not exist: {e2}")

def main():
    """Main function"""
    create_schema()

if __name__ == "__main__":
    main()
