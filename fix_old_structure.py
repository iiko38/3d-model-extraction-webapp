#!/usr/bin/env python3
"""
Fix old file structure by moving files from dwg/zip/skp directories to proper structure
"""

import shutil
from pathlib import Path

def main():
    root = Path("./library")
    
    # Find all files in old structure (dwg, zip, skp directories)
    old_structure_files = []
    for file_path in root.rglob("*"):
        if file_path.is_file():
            parent_dir = file_path.parent.name
            if parent_dir in ["dwg", "zip", "skp", "rfa", "rvt"]:
                old_structure_files.append(file_path)
    
    print(f"Found {len(old_structure_files)} files in old structure")
    
    # Move files to proper structure
    for file_path in old_structure_files:
        # Determine file type from parent directory
        parent_dir = file_path.parent.name
        file_type = parent_dir
        
        # Find the product directory (go up until we find a directory that's not a file type)
        current_dir = file_path.parent
        while current_dir.parent != root and current_dir.parent.name in ["dwg", "zip", "skp", "rfa", "rvt", "extracted"]:
            current_dir = current_dir.parent
        
        # The current_dir should be the product directory
        product_dir = current_dir
        
        # Create file_type directory under the product directory
        file_type_dir = product_dir / file_type
        file_type_dir.mkdir(exist_ok=True)
        
        # Move file to proper location
        target_path = file_type_dir / file_path.name
        if not target_path.exists():
            shutil.move(str(file_path), str(target_path))
            print(f"Moved {file_path} -> {target_path}")
        else:
            print(f"Target exists, skipping {file_path}")
    
    # Remove empty old directories
    for file_path in old_structure_files:
        parent_dir = file_path.parent
        if parent_dir.exists() and not any(parent_dir.iterdir()):
            parent_dir.rmdir()
            print(f"Removed empty directory {parent_dir}")

if __name__ == "__main__":
    main()
