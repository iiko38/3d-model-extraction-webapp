"""
Minimal FastAPI app for Vercel deployment
Simplified version to avoid import and configuration issues
"""
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase not available")

# Initialize Supabase if available
supabase = None
if SUPABASE_AVAILABLE and os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY'):
    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )
        print("✅ Supabase client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase: {e}")
        supabase = None

# Create FastAPI app
app = FastAPI(
    title="3D Model Library - Cloud Edition",
    version="2.0.0",
    docs_url=None,
    redoc_url=None
)

# Mount static files if they exist
try:
    if Path("app/static").exists():
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

# Setup Jinja2 templates if they exist
try:
    if Path("app/templates").exists():
        templates = Jinja2Templates(directory="app/templates")
        
        # Add custom Jinja filters
        def format_file_size(size_bytes: int) -> str:
            """Format file size in human readable format."""
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        
        templates.env.filters["format_size"] = format_file_size
    else:
        templates = None
except Exception as e:
    print(f"Warning: Could not setup templates: {e}")
    templates = None

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint with actual data"""
    if templates and supabase:
        try:
            # Get sample data from Supabase
            files_result = supabase.table('files').select('*').limit(20).execute()
            products_result = supabase.table('products').select('*').limit(10).execute()
            
            # Get unique values for filters
            brands_result = supabase.table('files').select('brand').execute()
            brands = list(set([f['brand'] for f in brands_result.data if f['brand']]))
            
            file_types_result = supabase.table('files').select('file_type').execute()
            file_types = list(set([f['file_type'] for f in file_types_result.data if f['file_type']]))
            
            return templates.TemplateResponse("warehouse_grid.html", {
                "request": request,
                "files": files_result.data,
                "products": products_result.data,
                "brands": brands,
                "file_types": file_types,
                "total_files": len(files_result.data),
                "total_products": len(products_result.data)
            })
        except Exception as e:
            return HTMLResponse(f"""
            <html>
                <head><title>3D Model Library</title></head>
                <body>
                    <h1>3D Model Library - Cloud Edition</h1>
                    <p>Database error: {e}</p>
                    <p>Environment variables:</p>
                    <ul>
                        <li>SUPABASE_URL: {os.getenv('SUPABASE_URL', 'Not set')}</li>
                        <li>SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY', 'Not set')[:20] if os.getenv('SUPABASE_ANON_KEY') else 'Not set'}...</li>
                    </ul>
                    <p>Supabase available: {SUPABASE_AVAILABLE}</p>
                    <p>Supabase initialized: {supabase is not None}</p>
                </body>
            </html>
            """)
    elif templates:
        return HTMLResponse(f"""
        <html>
            <head><title>3D Model Library</title></head>
            <body>
                <h1>3D Model Library - Cloud Edition</h1>
                <p>Template available but Supabase not connected</p>
                <p>Environment variables:</p>
                <ul>
                    <li>SUPABASE_URL: {os.getenv('SUPABASE_URL', 'Not set')}</li>
                    <li>SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY', 'Not set')[:20] if os.getenv('SUPABASE_ANON_KEY') else 'Not set'}...</li>
                </ul>
            </body>
        </html>
        """)
    else:
        return HTMLResponse("""
        <html>
            <head><title>3D Model Library</title></head>
            <body>
                <h1>3D Model Library - Cloud Edition</h1>
                <p>App is running! Templates not available.</p>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "message": "3D Model Library is running",
        "environment": {
            "supabase_url_set": bool(os.getenv('SUPABASE_URL')),
            "supabase_key_set": bool(os.getenv('SUPABASE_ANON_KEY')),
            "templates_available": templates is not None
        }
    })

@app.get("/api/test")
async def test_api():
    """Test API endpoint"""
    return JSONResponse({
        "message": "API is working",
        "timestamp": "2024-01-20T12:00:00Z"
    })

@app.get("/api/data")
async def get_data():
    """Get sample data from Supabase"""
    if not supabase:
        return JSONResponse({
            "error": "Supabase not available",
            "supabase_available": SUPABASE_AVAILABLE,
            "supabase_initialized": supabase is not None
        })
    
    try:
        # Get sample data
        files = supabase.table('files').select('*').limit(5).execute()
        products = supabase.table('products').select('*').limit(5).execute()
        
        return JSONResponse({
            "success": True,
            "files_count": len(files.data),
            "products_count": len(products.data),
            "sample_files": files.data[:3],
            "sample_products": products.data[:3]
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "supabase_available": SUPABASE_AVAILABLE,
            "supabase_initialized": supabase is not None
        })

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return HTMLResponse("""
    <html>
        <head><title>404 - Not Found</title></head>
        <body>
            <h1>404 - Page Not Found</h1>
            <p>The requested page could not be found.</p>
            <a href="/">Go back home</a>
        </body>
    </html>
    """)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return HTMLResponse(f"""
    <html>
        <head><title>500 - Internal Server Error</title></head>
        <body>
            <h1>500 - Internal Server Error</h1>
            <p>Something went wrong on our end.</p>
            <p>Error: {str(exc)}</p>
            <a href="/">Go back home</a>
        </body>
    </html>
    """)
