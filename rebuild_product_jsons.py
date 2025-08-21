#!/usr/bin/env python3
"""
Rebuild every product.json from the manifest
"""

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def load_manifest(manifest_path: Path) -> List[Dict]:
    """Load manifest JSONL file."""
    files = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            files.append(json.loads(line))
    return files


def group_by_product(files: List[Dict]) -> Dict[str, List[Dict]]:
    """Group files by (brand, product_slug)."""
    products = defaultdict(list)
    
    for file_record in files:
        brand = file_record['brand']
        product_slug = file_record['product_slug']
        product_key = f"{brand}:{product_slug}"
        products[product_key].append(file_record)
    
    return products


def dedupe_files_by_sha256(files: List[Dict]) -> List[Dict]:
    """Deduplicate files by SHA256 hash."""
    seen_hashes = set()
    unique_files = []
    
    for file_record in files:
        sha256 = file_record['sha256']
        if sha256 not in seen_hashes:
            seen_hashes.add(sha256)
            unique_files.append(file_record)
    
    return unique_files


def create_product_json_data(product_files: List[Dict]) -> Dict:
    """Create product.json data structure from file records."""
    if not product_files:
        return None
    
    # All files should have the same brand and product info
    first_file = product_files[0]
    brand = first_file['brand']
    product = first_file['product']
    product_slug = first_file['product_slug']
    
    # Deduplicate files by SHA256
    unique_files = dedupe_files_by_sha256(product_files)
    
    # Convert to product.json format
    files_data = []
    for file_record in unique_files:
        file_data = {
            "source_url": None,
            "stored_path": file_record['stored_path'],
            "file_type": file_record['file_type'],
            "ext": file_record['ext'],
            "sha256": file_record['sha256'],
            "size_bytes": file_record['size_bytes'],
            "variant": file_record.get('variant')
        }
        files_data.append(file_data)
    
    product_data = {
        "brand": brand,
        "product": product,
        "product_slug": product_slug,
        "category": None,
        "source_pages": [],
        "files": files_data,
        "updated_at": int(time.time())
    }
    
    return product_data


def rebuild_product_jsons(root_path: Path, manifest_path: Path, dry_run: bool = True) -> None:
    """Rebuild all product.json files from manifest."""
    print(f"Loading manifest from {manifest_path}")
    files = load_manifest(manifest_path)
    print(f"Loaded {len(files)} file records")
    
    print(f"Grouping by product...")
    products = group_by_product(files)
    print(f"Found {len(products)} products")
    
    print()
    
    created_count = 0
    updated_count = 0
    total_files = 0
    
    for product_key, product_files in products.items():
        brand, product_slug = product_key.split(':', 1)
        
        # Create product directory path
        product_dir = root_path / brand / product_slug
        json_path = product_dir / "product.json"
        
        # Create product.json data
        product_data = create_product_json_data(product_files)
        if not product_data:
            continue
        
        total_files += len(product_data['files'])
        
        if dry_run:
            print(f"Would {'create' if not json_path.exists() else 'update'} {json_path}")
            print(f"  Files: {len(product_data['files'])}")
        else:
            # Ensure directory exists
            product_dir.mkdir(parents=True, exist_ok=True)
            
            # Write product.json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2, ensure_ascii=False)
            
            if json_path.exists():
                updated_count += 1
            else:
                created_count += 1
    
    print()
    print("Summary:")
    print(f"  Products processed: {len(products)}")
    if not dry_run:
        print(f"  product.json created: {created_count}")
        print(f"  product.json updated: {updated_count}")
    print(f"  Total files: {total_files}")


def main():
    parser = argparse.ArgumentParser(description='Rebuild product.json files from manifest')
    parser.add_argument('--root', default='./library', help='Library root directory')
    parser.add_argument('--manifest', default='manifest.jsonl', help='Input manifest file')
    parser.add_argument('--write', action='store_true', help='Actually write files (default is dry-run)')
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    manifest_path = Path(args.manifest)
    
    if not root_path.exists():
        print(f"Error: Root directory {root_path} does not exist")
        return 1
    
    if not manifest_path.exists():
        print(f"Error: Manifest file {manifest_path} does not exist")
        return 1
    
    print(f"Rebuilding product.json files")
    print(f"Root: {root_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Mode: {'WRITE' if args.write else 'DRY-RUN'}")
    print()
    
    rebuild_product_jsons(root_path, manifest_path, dry_run=not args.write)
    
    return 0


if __name__ == "__main__":
    exit(main())


