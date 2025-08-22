"""
Cloud-optimized FastAPI application for Vercel deployment
Uses Supabase for database and local file storage for 3D files
"""

import os
import zipfile
import io
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Request, HTTPException, Depends, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel
import json

from .db_supabase import db
from .settings_cloud import settings
from .thumbnail_service import thumbnail_service

# Validate configuration on startup
if not settings.validate_config():
    raise ValueError("Invalid cloud configuration")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    docs_url=None,
    redoc_url=None
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount thumbnails directory (if exists)
if Path("static/thumbnails").exists():
    app.mount("/thumbnails", StaticFiles(directory="static/thumbnails"), name="thumbnails")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Pydantic models
class FileUpdate(BaseModel):
    field: str
    value: str

class BulkUpdate(BaseModel):
    sha256s: List[str]
    updates: dict

# Custom Jinja filters
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

@app.get("/", response_class=HTMLResponse)
async def warehouse_grid(request: Request,
                        search: Optional[str] = None,
                        brand: Optional[str] = None,
                        file_type: Optional[str] = None,
                        furniture_type: Optional[str] = None,
                        status: Optional[str] = None,
                        url_health: Optional[str] = None,
                        page: int = 1,
                        per_page: int = 50):
    """Main warehouse grid with advanced filtering."""
    
    # Get files with filters
    result = db.get_files_with_filters(
        search=search,
        brand=brand,
        file_type=file_type,
        furniture_type=furniture_type,
        status=status,
        url_health=url_health,
        page=page,
        per_page=per_page
    )
    
    # Get filter options
    brands = db.get_unique_values('brand', 'files')
    file_types = db.get_unique_values('file_type')
    furniture_types = db.get_unique_values('furniture_type')
    statuses = db.get_unique_values('status')
    url_healths = db.get_unique_values('url_health')
    
    return templates.TemplateResponse("warehouse_grid.html", {
        "request": request,
        "files": result['files'],
        "pagination": result['pagination'],
        "filters": {
            "search": search,
            "brand": brand,
            "file_type": file_type,
            "furniture_type": furniture_type,
            "status": status,
            "url_health": url_health
        },
        "filter_options": {
            "brands": brands,
            "file_types": file_types,
            "furniture_types": furniture_types,
            "statuses": statuses,
            "url_healths": url_healths
        }
    })

@app.get("/cards", response_class=HTMLResponse)
async def product_cards(request: Request,
                       search: Optional[str] = None,
                       brand: Optional[str] = None,
                       page: int = 1,
                       per_page: int = 20):
    """Product cards view with images."""
    
    # Get products with filters
    result = db.get_products(
        search=search,
        brand=brand,
        page=page,
        per_page=per_page
    )
    
    # Get filter options
    brands = db.get_unique_values('brand', 'products')
    
    return templates.TemplateResponse("warehouse_cards.html", {
        "request": request,
        "products": result['products'],
        "pagination": {
            "page": result['page'],
            "per_page": result['per_page'],
            "total": result['total'],
            "pages": result['pages']
        },
        "filters": {
            "search": search,
            "brand": brand
        },
        "filter_options": {
            "brands": brands
        }
    })

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """Statistics dashboard."""
    
    stats = db.get_stats()
    
    return templates.TemplateResponse("stats_refactored.html", {
        "request": request,
        "stats": stats
    })

@app.get("/thumbnails", response_class=HTMLResponse)
async def thumbnails_page(request: Request):
    """Thumbnails management page."""
    
    # Get all images
    images_response = db.supabase.table('images').select('*').execute()
    images = images_response.data
    
    return templates.TemplateResponse("thumbnails.html", {
        "request": request,
        "images": images
    })

@app.get("/database-tables", response_class=HTMLResponse)
async def database_tables(request: Request):
    """Database tables browser."""
    
    # Get sample data from each table
    products = db.supabase.table('products').select('*').limit(10).execute()
    files = db.supabase.table('files').select('*').limit(10).execute()
    images = db.supabase.table('images').select('*').limit(10).execute()
    
    return templates.TemplateResponse("database_tables.html", {
        "request": request,
        "products": products.data,
        "files": files.data,
        "images": images.data
    })

@app.get("/file")
async def serve_file(path: str):
    """Serve 3D files from local storage."""
    
    # Security check - prevent path traversal
    if ".." in path or path.startswith("/"):
        raise HTTPException(400, "Invalid file path")
    
    file_path = settings.LOCAL_FILE_ROOT / path
    
    # Ensure file is within allowed directory
    try:
        file_path = file_path.resolve()
        if not file_path.is_relative_to(settings.LOCAL_FILE_ROOT):
            raise HTTPException(400, "Path traversal blocked")
    except (ValueError, RuntimeError):
        raise HTTPException(400, "Invalid file path")
    
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    
    # Determine content type based on file extension
    content_type = "application/octet-stream"
    if file_path.suffix.lower() in ['.skp', '.dwg', '.rfa', '.rvt']:
        content_type = "application/octet-stream"
    
    return FileResponse(
        file_path,
        filename=file_path.name,
        media_type=content_type
    )

@app.get("/download/{sha256}")
async def download_file(sha256: str):
    """Download file by SHA256 hash."""
    
    file_data = db.get_file_by_sha256(sha256)
    if not file_data:
        raise HTTPException(404, "File not found")
    
    file_path = settings.LOCAL_FILE_ROOT / file_data['stored_path']
    
    if not file_path.exists():
        raise HTTPException(404, "File not found on disk")
    
    return FileResponse(
        file_path,
        filename=f"{file_data['name']}.{file_data['ext']}",
        media_type="application/octet-stream"
    )

# API Endpoints
@app.get("/api/products")
async def api_products(search: Optional[str] = None,
                      brand: Optional[str] = None,
                      page: int = 1,
                      per_page: int = 20):
    """API endpoint for products."""
    return db.get_products(search=search, brand=brand, page=page, per_page=per_page)

@app.get("/api/products/{product_uid}")
async def api_product_detail(product_uid: str):
    """API endpoint for product detail."""
    product = db.get_product_detail(product_uid)
    if not product:
        raise HTTPException(404, "Product not found")
    
    files = db.get_product_files(product_uid)
    images = db.get_product_images(product_uid)
    
    return {
        "product": product,
        "files": files,
        "images": images
    }

@app.get("/api/files")
async def api_files(search: Optional[str] = None,
                   brand: Optional[str] = None,
                   file_type: Optional[str] = None,
                   page: int = 1,
                   per_page: int = 50):
    """API endpoint for files."""
    return db.get_files_with_filters(
        search=search,
        brand=brand,
        file_type=file_type,
        page=page,
        per_page=per_page
    )

@app.get("/api/stats")
async def api_stats():
    """API endpoint for statistics."""
    return db.get_stats()

@app.get("/api/images/{product_uid}")
async def api_product_images(product_uid: str, status: Optional[str] = None):
    """API endpoint for product images."""
    images = db.get_product_images(product_uid, status=status)
    return {"images": images}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Vercel."""
    try:
        # Test database connection
        test_response = db.supabase.table('products').select('product_uid').limit(1).execute()
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": settings.APP_VERSION,
        "environment": "cloud"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
