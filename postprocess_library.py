#!/usr/bin/env python3
"""
Post-process the library to fix folder structure and ensure every product has a product.json
"""

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple


def normalize_folder_layout(root: Path, dry_run: bool = True) -> List[Tuple[Path, Path]]:
    """Detect and move letter-bucket folders up one level."""
    moves = []
    
    for brand_dir in root.iterdir():
        if not brand_dir.is_dir():
            continue
            
        for item in brand_dir.iterdir():
            if not item.is_dir():
                continue
                
            # Check if this is a single letter directory (a-z)
            if len(item.name) == 1 and item.name.isalpha():
                letter_dir = item
                
                # Move all product folders up one level
                for product_dir in letter_dir.iterdir():
                    if not product_dir.is_dir():
                        continue
                        
                    target_path = brand_dir / product_dir.name
                    
                    if target_path.exists():
                        # Handle collision by merging contents
                        if not dry_run:
                            merge_directories(product_dir, target_path)
                        moves.append((product_dir, target_path))
                    else:
                        if not dry_run:
                            shutil.move(str(product_dir), str(target_path))
                        moves.append((product_dir, target_path))
                
                # Remove empty letter directory
                if not dry_run and not any(letter_dir.iterdir()):
                    letter_dir.rmdir()
    
    return moves


def merge_directories(source: Path, target: Path) -> None:
    """Merge source directory into target, handling file conflicts."""
    for item in source.iterdir():
        target_item = target / item.name
        
        if target_item.exists():
            if item.is_file():
                # Check if files are different by hash
                if not files_identical(item, target_item):
                    # Rename with -dup-{n} suffix
                    counter = 1
                    while target_item.exists():
                        stem = target_item.stem
                        suffix = target_item.suffix
                        target_item = target_item.parent / f"{stem}-dup-{counter}{suffix}"
                        counter += 1
                    shutil.move(str(item), str(target_item))
            elif item.is_dir():
                merge_directories(item, target_item)
        else:
            shutil.move(str(item), str(target_item))


def files_identical(file1: Path, file2: Path) -> bool:
    """Compare two files by SHA256 hash."""
    try:
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        return hash1 == hash2
    except Exception:
        return False


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def infer_file_type_from_extension(ext: str) -> str:
    """Infer file type from extension."""
    ext = ext.lower()
    if ext == ".skp":
        return "sketchup"
    elif ext == ".dwg":
        return "autocad"  # Will be refined to autocad_3d if we can determine
    elif ext in [".zip", ".rfa", ".rvt"]:
        return "revit"
    elif ext == ".obj":
        return "obj"
    elif ext == ".fbx":
        return "fbx"
    elif ext == ".glb":
        return "glb"
    elif ext == ".gltf":
        return "gltf"
    elif ext == ".3ds":
        return "3ds"
    elif ext == ".3dm":
        return "3dm"
    elif ext == ".sif":
        return "sif"
    else:
        return "unknown"


def build_product_index(root: Path, allowed_extensions: Set[str]) -> Dict[str, Dict]:
    """Build an in-memory index of all products and their files."""
    products = {}
    
    for brand_dir in root.iterdir():
        if not brand_dir.is_dir():
            continue
            
        brand = brand_dir.name
        
        for product_dir in brand_dir.iterdir():
            if not product_dir.is_dir():
                continue
                
            # Skip if this is not a product directory (e.g., has subdirectories that look like file types)
            product_name = product_dir.name
            product_slug = product_name
            
            # Check if this looks like a product directory (has files with allowed extensions, file type subdirectories, or variant subdirectories)
            has_files = any(
                item.is_file() and item.suffix.lower() in allowed_extensions
                for item in product_dir.iterdir()
            )
            has_file_types = any(
                subdir.is_dir() and subdir.name in ["revit", "sketchup", "autocad", "autocad_3d", "obj", "fbx", "glb", "gltf", "3ds", "3dm", "sif"]
                for subdir in product_dir.iterdir()
            )
            has_variants = any(
                subdir.is_dir() and not subdir.name in ["revit", "sketchup", "autocad", "autocad_3d", "obj", "fbx", "glb", "gltf", "3ds", "3dm", "sif", "extracted"]
                for subdir in product_dir.iterdir()
            )
            
            if not (has_files or has_file_types or has_variants):
                continue
                
            product_key = f"{brand}:{product_slug}"
            products[product_key] = {
                "brand": brand,
                "product": product_name.replace("-", " "),
                "product_slug": product_slug,
                "category": None,
                "source_pages": [],
                "files": [],
                "path": product_dir
            }
            
            # Scan all files in this product
            for file_path in product_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                    
                ext = file_path.suffix.lower()
                if ext not in allowed_extensions:
                    continue
                    
                # Determine file type and variant from path
                relative_path = file_path.relative_to(product_dir)
                path_parts = relative_path.parts
                
                file_type = None
                variant = None
                
                if len(path_parts) >= 2:
                    # Check if first part is a variant
                    if path_parts[0] not in ["revit", "sketchup", "autocad", "autocad_3d", "obj", "fbx", "glb", "gltf", "3ds", "3dm", "sif"]:
                        variant = path_parts[0]
                        if len(path_parts) >= 2:
                            file_type = path_parts[1]
                    else:
                        file_type = path_parts[0]
                
                # Infer file type from extension if not found in path
                if not file_type:
                    file_type = infer_file_type_from_extension(ext)
                
                # Compute file hash and size
                try:
                    sha256 = compute_file_hash(file_path)
                    size_bytes = file_path.stat().st_size
                except Exception as e:
                    print(f"Warning: Could not process {file_path}: {e}")
                    continue
                
                # Store path as POSIX
                stored_path = str(relative_path).replace("\\", "/")
                
                file_record = {
                    "source_url": None,
                    "stored_path": stored_path,
                    "file_type": file_type,
                    "ext": ext,
                    "sha256": sha256,
                    "size_bytes": size_bytes,
                    "variant": variant
                }
                
                products[product_key]["files"].append(file_record)
    
    return products


def update_product_json(product_path: Path, product_data: Dict, dry_run: bool = True) -> bool:
    """Write or merge product.json for a product."""
    json_path = product_path / "product.json"
    
    # Load existing data if it exists
    existing_data = None
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing {json_path}: {e}")
    
    # Prepare new data
    new_data = {
        "brand": product_data["brand"],
        "product": product_data["product"],
        "product_slug": product_data["product_slug"],
        "category": product_data.get("category"),
        "source_pages": existing_data.get("source_pages", []) if existing_data else [],
        "files": product_data["files"],
        "updated_at": int(time.time())
    }
    
    # Merge files if existing data
    if existing_data and "files" in existing_data:
        existing_files = {f["sha256"]: f for f in existing_data["files"]}
        new_files = {f["sha256"]: f for f in new_data["files"]}
        
        # Merge, preferring new data but keeping existing source_url if present
        merged_files = []
        for sha256, file_data in new_files.items():
            if sha256 in existing_files:
                # Keep existing source_url if present
                if existing_files[sha256].get("source_url"):
                    file_data["source_url"] = existing_files[sha256]["source_url"]
            merged_files.append(file_data)
        
        new_data["files"] = merged_files
    
    if not dry_run:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser(description='Post-process library folder structure and product.json files')
    parser.add_argument('--root', default='./library', help='Library root directory')
    parser.add_argument('--allow-ext', default='.zip,.rfa,.rvt,.skp,.dwg,.obj,.fbx,.glb,.gltf,.3ds,.3dm,.sif',
                       help='Comma-separated list of allowed file extensions')
    parser.add_argument('--write', action='store_true', help='Actually write changes (default is dry-run)')
    
    args = parser.parse_args()
    
    root = Path(args.root)
    if not root.exists():
        print(f"Error: Root directory {root} does not exist")
        return 1
    
    allowed_extensions = set(args.allow_ext.split(','))
    
    print(f"Post-processing library at {root}")
    print(f"Allowed extensions: {allowed_extensions}")
    print(f"Mode: {'WRITE' if args.write else 'DRY-RUN'}")
    print()
    
    # Step 1: Normalize folder layout
    print("1. Normalizing folder layout...")
    moves = normalize_folder_layout(root, dry_run=not args.write)
    print(f"   Found {len(moves)} moves to perform")
    for source, target in moves:
        print(f"   {source} -> {target}")
    print()
    
    # Step 2: Build product index
    print("2. Building product index...")
    products = build_product_index(root, allowed_extensions)
    print(f"   Found {len(products)} products")
    print()
    
    # Step 3: Update product.json files
    print("3. Updating product.json files...")
    created_count = 0
    updated_count = 0
    total_files = 0
    
    for product_key, product_data in products.items():
        product_path = product_data["path"]
        json_path = product_path / "product.json"
        
        if json_path.exists():
            updated_count += 1
        else:
            created_count += 1
        
        total_files += len(product_data["files"])
        
        if args.write:
            update_product_json(product_path, product_data, dry_run=False)
        else:
            print(f"   Would {'create' if not json_path.exists() else 'update'} {json_path}")
    
    print()
    print("Summary:")
    print(f"  Products processed: {len(products)}")
    print(f"  product.json created: {created_count}")
    print(f"  product.json updated: {updated_count}")
    print(f"  Files indexed: {total_files}")
    print(f"  Moves performed: {len(moves) if args.write else 0}")
    
    return 0


if __name__ == "__main__":
    exit(main())
