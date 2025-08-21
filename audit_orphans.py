#!/usr/bin/env python3
"""
Audit orphan files - find files on disk that aren't in the manifest
"""

from pathlib import Path
import json
import sys

def main():
    root = Path("library")
    manifest = Path("manifest.jsonl")
    
    if not manifest.exists():
        print("Error: manifest.jsonl not found")
        return 1
    
    # Load all stored_paths from manifest
    seen = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        seen.add(r["stored_path"])
    
    print(f"Files in manifest: {len(seen)}")
    
    # Find files on disk not in manifest
    missing = []
    for p in root.rglob("*"):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            # ignore product.json and obvious non-assets
            if rel.endswith("product.json"): 
                continue
            if rel not in seen:
                missing.append(rel)
    
    print(f"Orphan files not in manifest: {len(missing)}")
    for x in missing[:50]:
        print(" -", x)
    
    if len(missing) > 50:
        print(f" ... and {len(missing) - 50} more")
    
    return 0

if __name__ == "__main__":
    exit(main())
