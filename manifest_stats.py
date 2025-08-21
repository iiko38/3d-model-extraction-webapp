#!/usr/bin/env python3
"""
Analyze manifest statistics
"""

import json
import sys
from collections import Counter

def main():
    m = sys.argv[1] if len(sys.argv) > 1 else "manifest.jsonl"
    prods = set()
    types = Counter()
    
    with open(m, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            prods.add((r["brand"], r["product_slug"]))
            types[r["file_type"]] += 1
    
    print("manifest products:", len(prods))
    print("by type:", dict(types))
    
    # Show some sample products
    print("\nSample products:")
    for i, (brand, slug) in enumerate(sorted(prods)):
        if i < 10:
            print(f"  {brand}: {slug}")
        else:
            print(f"  ... and {len(prods) - 10} more")
            break

if __name__ == "__main__":
    main()


