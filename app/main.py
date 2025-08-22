"""
Refactored 3D Warehouse Application
Features: Filterable grid, inline editing, FTS5 search, bulk actions, bundle API
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

from .db_refactored import db
from .settings import APP_TITLE, APP_VERSION, LIB_ROOT
from .thumbnail_service import thumbnail_service

# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    docs_url=None,
    redoc_url=None
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount thumbnails directory
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
    brands = db.get_unique_values('brand', 'products')
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

@app.get("/api/files/{sha256}")
async def get_file_api(sha256: str):
    """Get file data for API."""
    file_data = db.get_file_by_sha256(sha256)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    return file_data

@app.put("/api/files/{sha256}")
async def update_file_api(sha256: str, update: FileUpdate):
    """Update a single file field."""
    success = db.update_file_field(sha256, update.field, update.value)
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")
    return {"success": True}

@app.post("/api/files/bulk-update")
async def bulk_update_files_api(update: BulkUpdate):
    """Bulk update multiple files."""
    try:
        # Deduplicate sha256s to prevent issues
        unique_sha256s = list(set(update.sha256s))
        success = db.bulk_update_files(unique_sha256s, update.updates)
        if not success:
            raise HTTPException(status_code=500, detail="Bulk update failed")
        return {"success": True, "updated_count": len(unique_sha256s)}
    except Exception as e:
        print(f"Bulk update API error: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")

@app.get("/api/bundle/{product_uid}")
async def get_product_bundle(product_uid: str, 
                           formats: Optional[str] = None,
                           download: bool = False):
    """Get product bundle with preferred formats."""
    
    # Parse preferred formats
    preferred_formats = None
    if formats:
        preferred_formats = formats.split(',')
    
    files = db.get_bundle_files(product_uid, preferred_formats)
    
    if not files:
        raise HTTPException(status_code=404, detail="No files found for product")
    
    if download:
        # Create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_data in files:
                file_path = LIB_ROOT / file_data['stored_path']
                if file_path.exists():
                    zip_file.write(file_path, file_data['stored_path'])
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={product_uid}_bundle.zip"}
        )
    
    return {
        "product_uid": product_uid,
        "files": files,
        "total_files": len(files),
        "total_size": sum(f['size_bytes'] for f in files)
    }

@app.get("/api/search")
async def search_files_api(q: str, limit: int = 50):
    """Search files using FTS5."""
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query too short")
    
    files = db.search_files(q.strip(), limit)
    return {
        "query": q,
        "files": files,
        "total": len(files)
    }

@app.get("/api/stats")
async def get_stats_api():
    """Get system statistics."""
    return db.get_stats()

@app.post("/api/thumbnails/download")
async def download_thumbnails_api(background_tasks: BackgroundTasks):
    """Trigger thumbnail download for all checked URLs."""
    background_tasks.add_task(thumbnail_service.download_all_thumbnails)
    return {"message": "Thumbnail download started in background"}

@app.get("/api/thumbnails/status")
async def get_thumbnail_status_api():
    """Get thumbnail download status and statistics."""
    files_needing_thumbnails = thumbnail_service.get_files_needing_thumbnails()
    
    # Count cached thumbnails
    cache_dir = thumbnail_service.cache_dir / "original"
    cached_count = len(list(cache_dir.glob("*.jpg"))) if cache_dir.exists() else 0
    
    return {
        "files_needing_thumbnails": len(files_needing_thumbnails),
        "cached_thumbnails": cached_count,
        "sample_files": files_needing_thumbnails[:5] if files_needing_thumbnails else []
    }

@app.post("/api/thumbnails/cleanup")
async def cleanup_thumbnails_api():
    """Clean up orphaned thumbnail files."""
    removed_count = thumbnail_service.cleanup_orphaned_thumbnails()
    return {"message": f"Cleaned up {removed_count} orphaned thumbnails"}

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """Statistics page."""
    stats = db.get_stats()
    return templates.TemplateResponse("stats_refactored.html", {
        "request": request,
        "stats": stats
    })

@app.get("/thumbnails", response_class=HTMLResponse)
async def thumbnails_page(request: Request):
    """Thumbnail management page."""
    # Get thumbnail status
    files_needing_thumbnails = thumbnail_service.get_files_needing_thumbnails()
    
    # Count cached thumbnails
    cache_dir = thumbnail_service.cache_dir / "original"
    cached_count = len(list(cache_dir.glob("*.jpg"))) if cache_dir.exists() else 0
    
    # Get sample files
    sample_files = files_needing_thumbnails[:10] if files_needing_thumbnails else []
    
    return templates.TemplateResponse("thumbnails.html", {
        "request": request,
        "files_needing_thumbnails": len(files_needing_thumbnails),
        "cached_thumbnails": cached_count,
        "sample_files": sample_files
    })

@app.get("/cards", response_class=HTMLResponse)
async def warehouse_cards(request: Request,
                         search: Optional[str] = None,
                         brand: Optional[str] = None,
                         furniture_type: Optional[str] = None,
                         status: Optional[str] = None,
                         url_health: Optional[str] = None,
                         urls_checked: Optional[str] = None,
                         page: int = 1,
                         per_page: int = 20):
    """Card view with variant grouping."""
    
    # Get variants with filters
    result = db.get_variants_with_filters(
        search=search,
        brand=brand,
        furniture_type=furniture_type,
        status=status,
        url_health=url_health,
        urls_checked=urls_checked,
        page=page,
        per_page=per_page
    )
    
    # Get filter options
    brands = db.get_unique_values('brand', 'products')
    furniture_types = db.get_unique_values('furniture_type')
    statuses = db.get_unique_values('status')
    url_healths = db.get_unique_values('url_health')
    
    # Calculate total files
    total_files = sum(len(variant['files']) for variant in result['variants'])
    
    return templates.TemplateResponse("warehouse_cards.html", {
        "request": request,
        "variants": result['variants'],
        "pagination": result['pagination'],
        "total_files": total_files,
        "filters": {
            "search": search,
            "brand": brand,
            "furniture_type": furniture_type,
            "status": status,
            "url_health": url_health,
            "urls_checked": urls_checked
        },
        "filter_options": {
            "brands": brands,
            "furniture_types": furniture_types,
            "statuses": statuses,
            "url_healths": url_healths
        }
    })

@app.get("/api/variants/{product_uid}/{variant}")
async def get_variant_api(product_uid: str, variant: str):
    """Get variant data for editing."""
    variant_data = db.get_variant_data(product_uid, variant)
    if not variant_data:
        raise HTTPException(status_code=404, detail="Variant not found")
    return variant_data

@app.get("/database-tables", response_class=HTMLResponse)
async def database_tables_page(request: Request):
    """Database tables page showing raw data."""
    try:
        # Get raw data from all tables (limited for performance)
        files = db.run_query("""
            SELECT f.*, p.brand, p.name 
            FROM files f 
            LEFT JOIN products p ON f.product_uid = p.product_uid 
            LIMIT 50
        """)
        products = db.run_query("SELECT * FROM products LIMIT 50")
        
        # Try to get FTS5 data, but handle if it doesn't exist
        try:
            fts_data = db.run_query("SELECT * FROM files_fts LIMIT 50")
        except:
            fts_data = []
        
        # Get table counts
        files_count = db.run_query("SELECT COUNT(*) as count FROM files")[0]['count']
        products_count = db.run_query("SELECT COUNT(*) as count FROM products")[0]['count']
        
        try:
            fts_count = db.run_query("SELECT COUNT(*) as count FROM files_fts")[0]['count']
        except:
            fts_count = 0
        
        stats = {
            'files_count': files_count,
            'products_count': products_count,
            'fts_count': fts_count
        }
        
        return templates.TemplateResponse("database_tables.html", {
            "request": request,
            "files": files,
            "products": products,
            "fts_data": fts_data,
            "stats": stats
        })
    except Exception as e:
        # Return a simple error page if something goes wrong
        return templates.TemplateResponse("database_tables.html", {
            "request": request,
            "files": [],
            "products": [],
            "fts_data": [],
            "stats": {"files_count": 0, "products_count": 0, "fts_count": 0},
            "error": str(e)
        })

@app.get("/file/{sha256}")
async def download_file(sha256: str):
    """Download a file by SHA256."""
    file_data = db.get_file_by_sha256(sha256)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = LIB_ROOT / file_data['stored_path']
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=str(file_path),
        filename=f"{file_data['variant']}.{file_data['ext']}",
        media_type='application/octet-stream'
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        stats = db.get_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "total_files": stats.get('totals', {}).get('total_files', 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
