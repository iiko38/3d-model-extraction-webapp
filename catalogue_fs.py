#!/usr/bin/env python3
"""
Catalogue the filesystem into a clean manifest JSONL
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set


def slugify(name: str) -> str:
    """Convert name to lowercase snake_case."""
    # Convert to lowercase and replace non-alphanumeric with underscores
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', name.lower())
    # Remove leading/trailing underscores and squeeze multiple underscores
    slug = re.sub(r'_+', '_', slug.strip('_'))
    return slug


def infer_brand_from_filename(filename: str) -> Optional[str]:
    """Infer brand from filename prefix."""
    if filename.startswith('HMI_'):
        return 'herman_miller'
    elif filename.startswith('GGR_'):
        return 'geiger'
    elif filename.startswith('NTO_'):
        return 'naughtone'
    return None


def normalize_brand(brand_folder: str) -> str:
    """Normalize brand folder name."""
    brand_lower = brand_folder.lower()
    if brand_lower in ['hm', 'hmi']:
        return 'herman_miller'
    return brand_folder


def infer_file_type_from_filename(filename: str, ext: str) -> str:
    """Infer file type from filename patterns."""
    filename_lower = filename.lower()
    
    # Check for 2D/3D patterns in DWG files
    if ext == '.dwg':
        if '_2d' in filename_lower:
            return 'autocad_2d'
        elif '_3d' in filename_lower:
            return 'autocad_3d'
        else:
            return 'autocad'
    
    # Extension-based mapping
    if ext in ['.rfa', '.rvt']:
        return 'revit'
    elif ext == '.skp':
        return 'sketchup'
    elif ext == '.sif':
        return 'sif'
    elif ext == '.zip':
        return 'revit'  # ZIPs are Revit archives
    
    # Generic extensions
    elif ext == '.obj':
        return 'obj'
    elif ext == '.fbx':
        return 'fbx'
    elif ext == '.glb':
        return 'glb'
    elif ext == '.gltf':
        return 'gltf'
    elif ext == '.3ds':
        return '3ds'
    elif ext == '.3dm':
        return '3dm'
    
    return 'unknown'


def is_canonical_file_type(file_type: str) -> bool:
    """Check if file_type is a canonical value."""
    canonical_types = {
        'revit', 'sketchup', 'autocad_3d', 'autocad_2d', 
        'autocad', 'sif', 'obj', 'fbx', 'glb', 'gltf', '3ds', '3dm'
    }
    return file_type in canonical_types


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def parse_path_structure(file_path: Path, root_path: Path) -> Dict:
    """Parse file path to extract brand, product, variant, file_type."""
    # Get relative path from root
    rel_path = file_path.relative_to(root_path)
    path_parts = rel_path.parts
    
    if len(path_parts) < 2:
        return None  # Invalid path structure
    
    # Brand is always the first part
    brand_folder = path_parts[0]
    brand = normalize_brand(brand_folder)
    
    # Check if second part is a single letter (letter bucket)
    has_letter_bucket = len(path_parts) > 2 and len(path_parts[1]) == 1 and path_parts[1].isalpha()
    
    if has_letter_bucket:
        # Structure: brand/letter/product/variant?/file_type?/filename
        product_folder = path_parts[2]
        remaining_parts = path_parts[3:]
    else:
        # Structure: brand/product/variant?/file_type?/filename
        product_folder = path_parts[1]
        remaining_parts = path_parts[2:]
    
    product_slug = slugify(product_folder)
    product_name = product_slug.replace('_', ' ')
    
    # Parse remaining parts
    variant = None
    file_type = None
    
    if len(remaining_parts) >= 2:
        # Check if first remaining part is a variant (not a file type)
        potential_variant = remaining_parts[0]
        if is_canonical_file_type(potential_variant):
            # First part is file type
            file_type = potential_variant
        else:
            # First part is variant, second might be file type
            variant = potential_variant
            if len(remaining_parts) >= 2:
                potential_file_type = remaining_parts[1]
                if is_canonical_file_type(potential_file_type):
                    file_type = potential_file_type
    
    # If no file_type found in path, infer from filename
    if not file_type:
        filename = file_path.name
        ext = file_path.suffix.lower()
        file_type = infer_file_type_from_filename(filename, ext)
    
    return {
        'brand': brand,
        'product': product_name,
        'product_slug': product_slug,
        'variant': variant,
        'file_type': file_type
    }


def catalogue_filesystem(root_path: Path, include_zip: bool = False) -> List[Dict]:
    """Catalogue all files in the filesystem."""
    allowed_extensions = {
        '.rfa', '.rvt', '.skp', '.dwg', '.obj', '.fbx', 
        '.glb', '.gltf', '.3ds', '.3dm', '.sif', '.zip'
    }
    
    if not include_zip:
        allowed_extensions.remove('.zip')
    
    files = []
    
    for file_path in root_path.rglob('*'):
        if not file_path.is_file():
            continue
        
        ext = file_path.suffix.lower()
        if ext not in allowed_extensions:
            continue
        
        # Skip ZIP files unless explicitly included
        if ext == '.zip' and not include_zip:
            continue
        
        # Parse path structure
        path_info = parse_path_structure(file_path, root_path)
        if not path_info:
            continue
        
        # Compute file hash and size
        try:
            sha256 = compute_file_hash(file_path)
            size_bytes = file_path.stat().st_size
        except Exception as e:
            print(f"Warning: Could not process {file_path}: {e}")
            continue
        
        # Get stored path as POSIX
        stored_path = str(file_path.relative_to(root_path)).replace('\\', '/')
        
        # Infer brand from filename if not already determined
        filename = file_path.name
        filename_brand = infer_brand_from_filename(filename)
        if filename_brand:
            path_info['brand'] = filename_brand
        
        # Create file record
        file_record = {
            'brand': path_info['brand'],
            'product': path_info['product'],
            'product_slug': path_info['product_slug'],
            'variant': path_info['variant'],
            'file_type': path_info['file_type'],
            'ext': ext,
            'stored_path': stored_path,
            'filename': filename,
            'size_bytes': size_bytes,
            'sha256': sha256,
            'source_url': None,
            'source_page': None
        }
        
        files.append(file_record)
    
    return files


def main():
    parser = argparse.ArgumentParser(description='Catalogue filesystem into clean manifest')
    parser.add_argument('--root', default='./library', help='Library root directory')
    parser.add_argument('--out', default='manifest.jsonl', help='Output manifest file')
    parser.add_argument('--include-zip', action='store_true', help='Include ZIP files in manifest')
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    if not root_path.exists():
        print(f"Error: Root directory {root_path} does not exist")
        return 1
    
    output_path = Path(args.out)
    
    print(f"Catalogueing filesystem at {root_path}")
    print(f"Include ZIP files: {args.include_zip}")
    print()
    
    # Catalogue files
    files = catalogue_filesystem(root_path, args.include_zip)
    
    # Write manifest
    with open(output_path, 'w', encoding='utf-8') as f:
        for file_record in files:
            f.write(json.dumps(file_record, ensure_ascii=False) + '\n')
    
    # Generate summary
    print(f"Emitted {len(files)} rows to {output_path}")
    print()
    
    # Summary by file type
    file_type_counts = {}
    for file_record in files:
        file_type = file_record['file_type']
        file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
    
    print("By file type:")
    for file_type, count in sorted(file_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {file_type}: {count}")
    print()
    
    # Summary by brand
    brand_counts = {}
    for file_record in files:
        brand = file_record['brand']
        brand_counts[brand] = brand_counts.get(brand, 0) + 1
    
    print("By brand:")
    for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {brand}: {count}")
    
    return 0


if __name__ == "__main__":
    exit(main())


