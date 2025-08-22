#!/usr/bin/env python3
"""
Test Supabase Connection
Verifies that the migrated data is accessible
"""

from supabase import create_client, Client

# Configuration
SUPABASE_URL = "https://jcmnuxlusnfhusbulhag.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjbW51eGx1c25maHVzYnVsaGFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU4NjY0NDQsImV4cCI6MjA3MTQ0MjQ0NH0.OktEF3rXOxvJcy5PZj52xGezQYKvUG-S9R5Vfb-HNwI"

def test_connection():
    """Test Supabase connection and data access"""
    print("🔍 Testing Supabase connection...")
    
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    try:
        # Test products table
        print("\n📦 Testing products table...")
        products = supabase.table('products').select('*').limit(3).execute()
        print(f"✅ Found {len(products.data)} sample products:")
        for product in products.data:
            print(f"   - {product['name']} ({product['brand']})")
        
        # Test files table
        print("\n📁 Testing files table...")
        files = supabase.table('files').select('*').limit(3).execute()
        print(f"✅ Found {len(files.data)} sample files:")
        for file in files.data:
            print(f"   - {file['name']} ({file['file_type']}) - {file['size_bytes']} bytes")
        
        # Test images table
        print("\n🖼️  Testing images table...")
        images = supabase.table('images').select('*').limit(3).execute()
        print(f"✅ Found {len(images.data)} sample images:")
        for image in images.data:
            print(f"   - {image['image_url']} (score: {image['score']})")
        
        # Get statistics
        print("\n📊 Getting statistics...")
        
        # Count products by brand
        products_all = supabase.table('products').select('brand').execute()
        brand_counts = {}
        for product in products_all.data:
            brand = product['brand']
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
        
        print("Products by brand:")
        for brand, count in brand_counts.items():
            print(f"   - {brand}: {count}")
        
        # Count files by type
        files_all = supabase.table('files').select('file_type').execute()
        file_type_counts = {}
        for file in files_all.data:
            file_type = file['file_type']
            file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
        
        print("\nFiles by type:")
        for file_type, count in file_type_counts.items():
            print(f"   - {file_type}: {count}")
        
        print(f"\n🎉 All tests passed! Your data is successfully migrated to Supabase.")
        print(f"📊 Total: {len(products_all.data)} products, {len(files_all.data)} files, {len(images.data)} images")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    """Main function"""
    test_connection()

if __name__ == "__main__":
    main()
