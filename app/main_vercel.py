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
    else:
        templates = None
except Exception as e:
    print(f"Warning: Could not setup templates: {e}")
    templates = None

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - simple health check"""
    if templates:
        try:
            return templates.TemplateResponse("warehouse_grid.html", {"request": request})
        except Exception as e:
            return HTMLResponse(f"""
            <html>
                <head><title>3D Model Library</title></head>
                <body>
                    <h1>3D Model Library - Cloud Edition</h1>
                    <p>Template error: {e}</p>
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
