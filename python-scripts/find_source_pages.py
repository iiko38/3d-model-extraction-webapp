#!/usr/bin/env python3
import json
import pathlib

def find_products_with_source_pages():
    """Find products that actually have source pages."""
    library_root = pathlib.Path("library")
    products_with_sources = []
    
    for product_file in library_root.rglob("product.json"):
        try:
            with open(product_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            source_pages = data.get('source_pages', [])
            if source_pages:
                products_with_sources.append({
                    'file': product_file,
                    'brand': data.get('brand', 'unknown'),
                    'product': data.get('product', 'unknown'),
                    'source_pages': source_pages
                })
                print(f"✓ {data['brand']}:{data['product']} - {len(source_pages)} source pages")
                for page in source_pages[:2]:  # Show first 2
                    print(f"  - {page}")
                if len(source_pages) > 2:
                    print(f"  ... and {len(source_pages) - 2} more")
                print()
        
        except Exception as e:
            print(f"Error reading {product_file}: {e}")
    
    print(f"\nTotal products with source pages: {len(products_with_sources)}")
    return products_with_sources

if __name__ == "__main__":
    find_products_with_source_pages()
