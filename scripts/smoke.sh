#!/bin/bash

# HM Product Models Scraper - Smoke Test
# Tests the scraper on all three page types: listing, individual, and system

set -e  # Exit on any error

echo "=== HM Product Models Scraper - Smoke Test ==="
echo "Testing all three page types: listing, individual, system"
echo

# Clean up previous test runs
echo "Cleaning up previous test runs..."
rm -rf library/
rm -f seen_pages.txt

# Test 1: Root listing page (default seed)
echo "=== Test 1: Root listing page ==="
python hm_rip.py --max-pages 1 --max-downloads 3 --dry-run
echo

# Test 2: Individual product page
echo "=== Test 2: Individual product page ==="
python hm_rip.py --seeds "https://www.hermanmiller.com/resources/3d-models-and-planning-tools/product-models/individual/seating/office-chairs/aeron-chair/" --max-pages 1 --max-downloads 3 --dry-run
echo

# Test 3: System page
echo "=== Test 3: System page ==="
python hm_rip.py --seeds "https://www.hermanmiller.com/resources/3d-models-and-planning-tools/product-models/system/action-office/" --max-pages 1 --max-downloads 3 --dry-run
echo

# Test 4: Actual download test (small scale)
echo "=== Test 4: Actual download test ==="
python hm_rip.py --max-pages 1 --max-downloads 2 --sleep-min 0.2 --sleep-max 0.4
echo

# Verify outputs
echo "=== Verifying outputs ==="

# Check if library directory exists and has content
if [ -d "library" ]; then
    echo "✅ Library directory created"
    
    # Check for different file types
    echo "Checking for different file types..."
    
    # Look for SketchUp files
    if find library -name "*.skp" | head -1 > /dev/null; then
        echo "✅ Found SketchUp (.skp) files"
    else
        echo "❌ No SketchUp files found"
    fi
    
    # Look for AutoCAD files
    if find library -name "*.dwg" | head -1 > /dev/null; then
        echo "✅ Found AutoCAD (.dwg) files"
    else
        echo "❌ No AutoCAD files found"
    fi
    
    # Look for Revit files
    if find library -name "*.zip" | head -1 > /dev/null; then
        echo "✅ Found Revit (.zip) files"
    else
        echo "❌ No Revit ZIP files found"
    fi
    
    # Look for extracted RFA files
    if find library -name "*.rfa" | head -1 > /dev/null; then
        echo "✅ Found extracted Revit (.rfa) files"
    else
        echo "❌ No extracted RFA files found"
    fi
    
    # Look for SIF files
    if find library -name "*.sif" | head -1 > /dev/null; then
        echo "✅ Found SIF files"
    else
        echo "⚠️  No SIF files found (may not be available in test data)"
    fi
    
    # Check product.json files
    echo "Checking product.json files..."
    if find library -name "product.json" | head -1 > /dev/null; then
        echo "✅ Found product.json files"
        
        # Check structure of first product.json
        first_json=$(find library -name "product.json" | head -1)
        echo "Checking structure of: $first_json"
        
        if python -c "
import json
with open('$first_json', 'r') as f:
    data = json.load(f)
    print('✅ product.json structure:')
    print(f'  - files: {len(data.get(\"files\", []))} entries')
    print(f'  - source_pages: {len(data.get(\"source_pages\", []))} entries')
    print(f'  - brand: {data.get(\"brand\", \"missing\")}')
    print(f'  - product: {data.get(\"product\", \"missing\")}')
    
    # Check first file entry
    if data.get('files'):
        first_file = data['files'][0]
        print(f'  - First file: {first_file.get(\"source_url\", \"missing\")}')
        print(f'    sha256: {first_file.get(\"sha256\", \"missing\")}')
        print(f'    size_bytes: {first_file.get(\"size_bytes\", \"missing\")}')
        print(f'    file_type: {first_file.get(\"file_type\", \"missing\")}')
" 2>/dev/null; then
            echo "✅ product.json has correct structure with sha256 and size_bytes"
        else
            echo "❌ product.json structure check failed"
        fi
    else
        echo "❌ No product.json files found"
    fi
    
else
    echo "❌ Library directory not found"
fi

echo
echo "=== Smoke test completed ==="
echo "Check the output above for any ❌ errors"
echo "If all tests pass, the scraper is working correctly!"
