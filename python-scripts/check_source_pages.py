#!/usr/bin/env python3
import json
import pathlib

def check_source_pages():
    library_root = pathlib.Path("library")
    
    products_with_source_pages = []
    products_without_source_pages = []
    
    for product_json in library_root.rglob("product.json"):
        try:
            with open(product_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            brand = data.get('brand', '')
            product = data.get('product', '')
            product_slug = data.get('product_slug', '')
            source_pages = data.get('source_pages', [])
            
            product_info = f"{brand}:{product_slug} ({product})"
            
            if source_pages:
                products_with_source_pages.append(product_info)
            else:
                products_without_source_pages.append(product_info)
                
        except Exception as e:
            print(f"Error reading {product_json}: {e}")
    
    print(f"Products WITH source pages ({len(products_with_source_pages)}):")
    for product in products_with_source_pages[:10]:  # Show first 10
        print(f"  {product}")
    
    print(f"\nProducts WITHOUT source pages ({len(products_without_source_pages)}):")
    for product in products_without_source_pages[:10]:  # Show first 10
        print(f"  {product}")
    
    # Check if zeph_stool has source pages
    zeph_path = library_root / "herman_miller" / "zeph_stool" / "product.json"
    if zeph_path.exists():
        with open(zeph_path, 'r', encoding='utf-8') as f:
            zeph_data = json.load(f)
        print(f"\nZeph stool source_pages: {zeph_data.get('source_pages', [])}")

if __name__ == "__main__":
    check_source_pages()
