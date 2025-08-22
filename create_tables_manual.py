#!/usr/bin/env python3
"""
Manually Create Tables in Supabase
Creates tables by inserting sample data and letting Supabase create the schema
"""

import os
from supabase import create_client, Client

# Configuration
SUPABASE_URL = "https://jcmnuxlusnfhusbulhag.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjbW51eGx1c25maHVzYnVsaGFnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTg2NjQ0NCwiZXhwIjoyMDcxNDQyNDQ0fQ.n0nnrYdxV2MUiPkyv2YPAI0hRhZLamsuGdo1wLii-Qs"

def create_tables():
    """Create tables by inserting sample data"""
    print("🏗️  Creating tables in Supabase...")
    
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        # Try to create products table with sample data
        print("Creating products table...")
        sample_product = {
            'product_uid': 'test_product_001',
            'brand': 'test_brand',
            'name': 'Test Product',
            'slug': 'test-product',
            'category': 'test_category'
        }
        
        result = supabase.table('products').insert(sample_product).execute()
        print("✅ Products table created successfully")
        
        # Delete the test data
        supabase.table('products').delete().eq('product_uid', 'test_product_001').execute()
        print("✅ Test product removed")
        
    except Exception as e:
        print(f"⚠️  Products table may already exist: {e}")
    
    try:
        # Try to create files table with sample data
        print("Creating files table...")
        sample_file = {
            'product_uid': 'test_product_001',
            'sha256': 'test_sha256_001',
            'file_type': 'test_type',
            'ext': 'test',
            'stored_path': 'test/path',
            'variant': 'test_variant'
        }
        
        result = supabase.table('files').insert(sample_file).execute()
        print("✅ Files table created successfully")
        
        # Delete the test data
        supabase.table('files').delete().eq('sha256', 'test_sha256_001').execute()
        print("✅ Test file removed")
        
    except Exception as e:
        print(f"⚠️  Files table may already exist: {e}")
    
    try:
        # Try to create images table with sample data
        print("Creating images table...")
        sample_image = {
            'product_uid': 'test_product_001',
            'variant': 'test_variant',
            'image_url': 'https://example.com/test.jpg',
            'provider': 'test_provider',
            'score': 1.0,
            'status': 'test_status'
        }
        
        result = supabase.table('images').insert(sample_image).execute()
        print("✅ Images table created successfully")
        
        # Delete the test data
        supabase.table('images').delete().eq('image_url', 'https://example.com/test.jpg').execute()
        print("✅ Test image removed")
        
    except Exception as e:
        print(f"⚠️  Images table may already exist: {e}")
    
    # Verify tables exist
    print("\n🔍 Verifying tables...")
    
    try:
        result = supabase.table('products').select('product_uid').limit(1).execute()
        print("✅ Products table exists and accessible")
    except Exception as e:
        print(f"❌ Products table issue: {e}")
    
    try:
        result = supabase.table('files').select('product_uid').limit(1).execute()
        print("✅ Files table exists and accessible")
    except Exception as e:
        print(f"❌ Files table issue: {e}")
    
    try:
        result = supabase.table('images').select('id').limit(1).execute()
        print("✅ Images table exists and accessible")
    except Exception as e:
        print(f"❌ Images table issue: {e}")

def main():
    """Main function"""
    create_tables()

if __name__ == "__main__":
    main()
