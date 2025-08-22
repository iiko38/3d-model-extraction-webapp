#!/usr/bin/env python3
"""
Check manifest for duplicates and inconsistencies
"""

import json
from pathlib import Path

def main():
    manifest_path = Path("manifest.jsonl")
    
    files = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            files.append(json.loads(line))
    
    print(f"Total files in manifest: {len(files)}")
    
    # Check for duplicate SHA256 hashes
    sha256_counts = {}
    for file_data in files:
        sha256 = file_data.get('sha256', '')
        sha256_counts[sha256] = sha256_counts.get(sha256, 0) + 1
    
    duplicates = {sha256: count for sha256, count in sha256_counts.items() if count > 1}
    if duplicates:
        print(f"\nDuplicate SHA256 hashes: {len(duplicates)}")
        for sha256, count in list(duplicates.items())[:5]:
            print(f"  {sha256}: {count} times")
    else:
        print("\nNo duplicate SHA256 hashes found")
    
    # Check for files with unusual file_type values
    unusual_types = []
    for file_data in files:
        file_type = file_data.get('file_type', '')
        if file_type not in ['revit', 'sketchup', 'autocad', 'autocad_3d', 'obj', 'fbx', 'glb', 'gltf', '3ds', '3dm', 'sif']:
            unusual_types.append(file_data)
    
    if unusual_types:
        print(f"\nFiles with unusual file_type: {len(unusual_types)}")
        for file_data in unusual_types[:5]:
            print(f"  {file_data.get('file_type')} ({file_data.get('ext')}): {file_data.get('stored_path')}")
    else:
        print("\nNo files with unusual file_type found")
    
    # Count by file type
    file_type_counts = {}
    for file_data in files:
        file_type = file_data.get('file_type', '')
        file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
    
    print(f"\nFile type distribution:")
    for file_type, count in sorted(file_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {file_type}: {count}")

if __name__ == "__main__":
    main()
