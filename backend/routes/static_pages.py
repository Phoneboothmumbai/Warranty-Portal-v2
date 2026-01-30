"""
Static Pages Routes - Public and Admin endpoints
================================================
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from models.static_pages import StaticPage, StaticPageUpdate, DEFAULT_PAGES
from utils.helpers import get_ist_isoformat

router = APIRouter()

_db = None

def init_db(database):
    global _db
    _db = database


async def ensure_default_pages():
    """Create default pages if they don't exist"""
    for slug, page_data in DEFAULT_PAGES.items():
        existing = await _db.static_pages.find_one({"slug": slug})
        if not existing:
            page = StaticPage(
                slug=slug,
                title=page_data["title"],
                content=page_data["content"]
            )
            await _db.static_pages.insert_one(page.model_dump())


# ==================== PUBLIC ENDPOINTS ====================

@router.get("/pages/{slug}")
async def get_public_page(slug: str):
    """Get a published static page by slug (public)"""
    # Ensure defaults exist
    await ensure_default_pages()
    
    page = await _db.static_pages.find_one(
        {"slug": slug, "is_published": True},
        {"_id": 0}
    )
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return page


@router.get("/pages")
async def list_public_pages():
    """List all published pages (public) - for footer links"""
    await ensure_default_pages()
    
    pages = await _db.static_pages.find(
        {"is_published": True},
        {"_id": 0, "slug": 1, "title": 1}
    ).to_list(20)
    
    return pages


# ==================== ADMIN ENDPOINTS ====================

@router.get("/admin/pages")
async def list_all_pages(admin: dict = None):  # Will add auth later
    """List all static pages (admin)"""
    await ensure_default_pages()
    
    pages = await _db.static_pages.find(
        {},
        {"_id": 0}
    ).to_list(50)
    
    return pages


@router.get("/admin/pages/{slug}")
async def get_page_for_edit(slug: str, admin: dict = None):
    """Get a static page for editing (admin)"""
    await ensure_default_pages()
    
    page = await _db.static_pages.find_one(
        {"slug": slug},
        {"_id": 0}
    )
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return page


@router.put("/admin/pages/{slug}")
async def update_page(slug: str, updates: StaticPageUpdate, admin: dict = None):
    """Update a static page (admin)"""
    page = await _db.static_pages.find_one({"slug": slug})
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await _db.static_pages.update_one(
        {"slug": slug},
        {"$set": update_data}
    )
    
    return await _db.static_pages.find_one({"slug": slug}, {"_id": 0})


@router.post("/admin/pages")
async def create_page(page: StaticPage, admin: dict = None):
    """Create a new static page (admin)"""
    existing = await _db.static_pages.find_one({"slug": page.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Page with this slug already exists")
    
    await _db.static_pages.insert_one(page.model_dump())
    
    return await _db.static_pages.find_one({"slug": page.slug}, {"_id": 0})


@router.delete("/admin/pages/{slug}")
async def delete_page(slug: str, admin: dict = None):
    """Delete a static page (admin) - only custom pages, not defaults"""
    if slug in DEFAULT_PAGES:
        raise HTTPException(status_code=400, detail="Cannot delete default pages. You can unpublish them instead.")
    
    result = await _db.static_pages.delete_one({"slug": slug})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return {"message": "Page deleted"}
