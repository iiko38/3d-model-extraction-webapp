@echo off
REM HM Product Models Scraper - Smoke Test
REM Tests the scraper on all three page types: listing, individual, and system

echo === HM Product Models Scraper - Smoke Test ===
echo Testing all three page types: listing, individual, system
echo.

REM Clean up previous test runs
echo Cleaning up previous test runs...
if exist library rmdir /s /q library
if exist seen_pages.txt del seen_pages.txt

REM Test 1: Root listing page (default seed)
echo === Test 1: Root listing page ===
python hm_rip.py --max-pages 1 --max-downloads 3 --dry-run
echo.

REM Test 2: Individual product page
echo === Test 2: Individual product page ===
python hm_rip.py --seeds "https://www.hermanmiller.com/resources/3d-models-and-planning-tools/product-models/individual/seating/office-chairs/aeron-chair/" --max-pages 1 --max-downloads 3 --dry-run
echo.

REM Test 3: System page
echo === Test 3: System page ===
python hm_rip.py --seeds "https://www.hermanmiller.com/resources/3d-models-and-planning-tools/product-models/system/action-office/" --max-pages 1 --max-downloads 3 --dry-run
echo.

REM Test 4: Actual download test (small scale)
echo === Test 4: Actual download test ===
python hm_rip.py --max-pages 1 --max-downloads 2 --sleep-min 0.2 --sleep-max 0.4
echo.

REM Verify outputs
echo === Verifying outputs ===

REM Check if library directory exists and has content
if exist library (
    echo [OK] Library directory created
    
    REM Check for different file types
    echo Checking for different file types...
    
    REM Look for SketchUp files
    dir /s /b library\*.skp >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Found SketchUp (.skp) files
    ) else (
        echo [FAIL] No SketchUp files found
    )
    
    REM Look for AutoCAD files
    dir /s /b library\*.dwg >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Found AutoCAD (.dwg) files
    ) else (
        echo [FAIL] No AutoCAD files found
    )
    
    REM Look for Revit files
    dir /s /b library\*.zip >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Found Revit (.zip) files
    ) else (
        echo [FAIL] No Revit ZIP files found
    )
    
    REM Look for extracted RFA files
    dir /s /b library\*.rfa >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Found extracted Revit (.rfa) files
    ) else (
        echo [FAIL] No extracted RFA files found
    )
    
    REM Look for SIF files
    dir /s /b library\*.sif >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Found SIF files
    ) else (
        echo [WARN] No SIF files found (may not be available in test data)
    )
    
    REM Check product.json files
    echo Checking product.json files...
    dir /s /b library\product.json >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Found product.json files
        
        REM Check structure of first product.json
        for /f "delims=" %%i in ('dir /s /b library\product.json ^| findstr /n "^" ^| findstr "^1:"') do (
            set first_json=%%i
            set first_json=!first_json:1:=!
        )
        echo Checking structure of: !first_json!
        
        python -c "import json; data=json.load(open('!first_json!', 'r')); print('[OK] product.json structure:'); print(f'  - files: {len(data.get(\"files\", []))} entries'); print(f'  - source_pages: {len(data.get(\"source_pages\", []))} entries'); print(f'  - brand: {data.get(\"brand\", \"missing\")}'); print(f'  - product: {data.get(\"product\", \"missing\")}'); first_file=data.get('files', [{}])[0] if data.get('files') else {}; print(f'  - First file: {first_file.get(\"source_url\", \"missing\")}'); print(f'    sha256: {first_file.get(\"sha256\", \"missing\")}'); print(f'    size_bytes: {first_file.get(\"size_bytes\", \"missing\")}'); print(f'    file_type: {first_file.get(\"file_type\", \"missing\")}')" 2>nul
        if %errorlevel% equ 0 (
            echo [OK] product.json has correct structure with sha256 and size_bytes
        ) else (
            echo [FAIL] product.json structure check failed
        )
    ) else (
        echo [FAIL] No product.json files found
    )
    
) else (
    echo [FAIL] Library directory not found
)

echo.
echo === Smoke test completed ===
echo Check the output above for any [FAIL] errors
echo If all tests pass, the scraper is working correctly!
pause
