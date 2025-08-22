#!/usr/bin/env python3
"""
Export a flat manifest of all files in the library
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List


def derive_variant_from_path(stored_path: str) -> str:
    """Derive variant from stored_path: the segment after product and before file_type if present."""
    parts = stored_path.split('/')
    if len(parts) >= 3:
        # Check if the first part looks like a variant (not a file type)
        potential_variant = parts[0]
        file_types = ["revit", "sketchup", "autocad", "autocad_3d", "obj", "fbx", "glb", "gltf", "3ds", "3dm", "sif", "extracted"]
        if potential_variant not in file_types:
            return potential_variant
    return ""


def export_manifest(root: Path, output_path: Path) -> None:
    """Export manifest of all files to JSONL or CSV format."""
    products = []
    
    # Find all product.json files
    for json_file in root.rglob("product.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                product_data = json.load(f)
            
            # Extract product info
            brand = product_data.get("brand", "")
            product = product_data.get("product", "")
            product_slug = product_data.get("product_slug", "")
            category = product_data.get("category")
            source_pages = product_data.get("source_pages", [])
            source_page = source_pages[0] if source_pages else ""
            
            # Process each file
            for file_data in product_data.get("files", []):
                variant = derive_variant_from_path(file_data.get("stored_path", ""))
                
                row = {
                    "brand": brand,
                    "product": product,
                    "product_slug": product_slug,
                    "category": category,
                    "variant": variant,
                    "file_type": file_data.get("file_type", ""),
                    "ext": file_data.get("ext", ""),
                    "stored_path": file_data.get("stored_path", ""),
                    "size_bytes": file_data.get("size_bytes", 0),
                    "sha256": file_data.get("sha256", ""),
                    "source_url": file_data.get("source_url"),
                    "source_page": source_page
                }
                products.append(row)
                
        except Exception as e:
            print(f"Warning: Could not process {json_file}: {e}")
    
    # Write output
    if output_path.suffix.lower() == ".csv":
        write_csv(products, output_path)
    else:
        write_jsonl(products, output_path)
    
    print(f"Exported {len(products)} file records to {output_path}")


def write_csv(products: List[Dict], output_path: Path) -> None:
    """Write products to CSV format."""
    if not products:
        return
    
    fieldnames = products[0].keys()
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)


def write_jsonl(products: List[Dict], output_path: Path) -> None:
    """Write products to JSONL format."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for product in products:
            f.write(json.dumps(product, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Export flat manifest of all files in library')
    parser.add_argument('--root', default='./library', help='Library root directory')
    parser.add_argument('--out', default='manifest.jsonl', help='Output file (CSV if .csv extension)')
    
    args = parser.parse_args()
    
    root = Path(args.root)
    if not root.exists():
        print(f"Error: Root directory {root} does not exist")
        return 1
    
    output_path = Path(args.out)
    
    print(f"Exporting manifest from {root} to {output_path}")
    export_manifest(root, output_path)
    
    return 0


if __name__ == "__main__":
    exit(main())
