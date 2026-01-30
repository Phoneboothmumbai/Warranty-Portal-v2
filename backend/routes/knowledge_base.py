"""
Knowledge Base Routes
=====================
API endpoints for managing knowledge base articles and categories
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import re

from services.auth import get_current_admin
from utils.tenant_scope import get_admin_org_id, scope_query
from models.knowledge_base import (
    KBCategory, KBArticle, KBCategoryCreate, KBCategoryUpdate,
    KBArticleCreate, KBArticleUpdate
)

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])

_db = None


def init_kb_router(database):
    """Initialize the router with database dependency"""
    global _db
    _db = database


def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text"""
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug[:100]


# ==================== PUBLIC ENDPOINTS ====================

@router.get("/public/categories")
async def list_public_categories():
    """List all public KB categories"""
    categories = await _db.kb_categories.find(
        {"is_public": True, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("order", 1).to_list(100)
    return categories


@router.get("/public/articles")
async def list_public_articles(
    category_id: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    featured: bool = False,
    limit: int = Query(20, le=100),
    skip: int = 0
):
    """List public published articles"""
    query = {"status": "published", "is_public": True, "is_deleted": {"$ne": True}}
    
    if category_id:
        query["category_id"] = category_id
    if tag:
        query["tags"] = tag
    if featured:
        query["is_featured"] = True
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    
    total = await _db.kb_articles.count_documents(query)
    articles = await _db.kb_articles.find(
        query,
        {"_id": 0, "content": 0}  # Exclude full content in list view
    ).sort([("is_featured", -1), ("published_at", -1)]).skip(skip).limit(limit).to_list(limit)
    
    return {"articles": articles, "total": total}


@router.get("/public/articles/{slug}")
async def get_public_article(slug: str):
    """Get a single public article by slug"""
    article = await _db.kb_articles.find_one(
        {"slug": slug, "status": "published", "is_public": True, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Increment view count
    await _db.kb_articles.update_one(
        {"slug": slug},
        {"$inc": {"views": 1}}
    )
    
    # Get category info
    if article.get("category_id"):
        category = await _db.kb_categories.find_one(
            {"id": article["category_id"]},
            {"_id": 0, "name": 1, "slug": 1}
        )
        article["category"] = category
    
    return article


@router.post("/public/articles/{article_id}/feedback")
async def submit_article_feedback(article_id: str, helpful: bool):
    """Submit feedback on whether article was helpful"""
    field = "helpful_yes" if helpful else "helpful_no"
    result = await _db.kb_articles.update_one(
        {"id": article_id, "is_deleted": {"$ne": True}},
        {"$inc": {field: 1}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"success": True}


# ==================== ADMIN ENDPOINTS - CATEGORIES ====================

@router.get("/admin/categories")
async def list_categories_admin(admin: dict = Depends(get_current_admin)):
    """List all KB categories (admin)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    categories = await _db.kb_categories.find(query, {"_id": 0}).sort("order", 1).to_list(100)
    
    # Add article count for each category
    for cat in categories:
        count = await _db.kb_articles.count_documents({
            "category_id": cat["id"],
            "is_deleted": {"$ne": True}
        })
        cat["article_count"] = count
    
    return categories


@router.post("/admin/categories")
async def create_category(data: KBCategoryCreate, admin: dict = Depends(get_current_admin)):
    """Create a KB category"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    # Generate slug if not provided
    slug = data.slug or generate_slug(data.name)
    
    # Check for duplicate slug
    existing = await _db.kb_categories.find_one({
        "slug": slug,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if existing:
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"
    
    category = KBCategory(
        organization_id=org_id,
        name=data.name,
        slug=slug,
        description=data.description,
        icon=data.icon,
        parent_id=data.parent_id,
        order=data.order,
        is_public=data.is_public
    )
    
    await _db.kb_categories.insert_one(category.model_dump())
    return category.model_dump()


@router.put("/admin/categories/{category_id}")
async def update_category(
    category_id: str,
    data: KBCategoryUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update a KB category"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": category_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    existing = await _db.kb_categories.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    await _db.kb_categories.update_one(query, {"$set": update_data})
    return await _db.kb_categories.find_one({"id": category_id}, {"_id": 0})


@router.delete("/admin/categories/{category_id}")
async def delete_category(category_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a KB category"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": category_id}
    query = scope_query(query, org_id)
    
    await _db.kb_categories.update_one(query, {"$set": {"is_deleted": True}})
    return {"success": True}


# ==================== ADMIN ENDPOINTS - ARTICLES ====================

@router.get("/admin/articles")
async def list_articles_admin(
    category_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    skip: int = 0,
    admin: dict = Depends(get_current_admin)
):
    """List all KB articles (admin)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    if category_id:
        query["category_id"] = category_id
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    
    total = await _db.kb_articles.count_documents(query)
    articles = await _db.kb_articles.find(
        query,
        {"_id": 0, "content": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Add category names
    for article in articles:
        if article.get("category_id"):
            cat = await _db.kb_categories.find_one(
                {"id": article["category_id"]},
                {"_id": 0, "name": 1}
            )
            article["category_name"] = cat.get("name") if cat else None
    
    return {"articles": articles, "total": total}


@router.get("/admin/articles/{article_id}")
async def get_article_admin(article_id: str, admin: dict = Depends(get_current_admin)):
    """Get a single article with full content (admin)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": article_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    article = await _db.kb_articles.find_one(query, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/admin/articles")
async def create_article(data: KBArticleCreate, admin: dict = Depends(get_current_admin)):
    """Create a KB article"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    # Generate slug if not provided
    slug = data.slug or generate_slug(data.title)
    
    # Check for duplicate slug
    existing = await _db.kb_articles.find_one({
        "slug": slug,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if existing:
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"
    
    # Generate excerpt if not provided
    excerpt = data.excerpt
    if not excerpt and data.content:
        # Strip HTML and take first 200 chars
        import re
        text = re.sub(r'<[^>]+>', '', data.content)
        excerpt = text[:200] + "..." if len(text) > 200 else text
    
    article = KBArticle(
        organization_id=org_id,
        category_id=data.category_id,
        title=data.title,
        slug=slug,
        content=data.content,
        excerpt=excerpt,
        tags=data.tags,
        status=data.status,
        is_featured=data.is_featured,
        is_public=data.is_public,
        author_id=admin.get("id"),
        author_name=admin.get("name") or admin.get("email")
    )
    
    if data.status == "published":
        article.published_at = datetime.utcnow().isoformat()
    
    await _db.kb_articles.insert_one(article.model_dump())
    return article.model_dump()


@router.put("/admin/articles/{article_id}")
async def update_article(
    article_id: str,
    data: KBArticleUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update a KB article"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": article_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    existing = await _db.kb_articles.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Article not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    # Set published_at if publishing for first time
    if data.status == "published" and existing.get("status") != "published":
        update_data["published_at"] = datetime.utcnow().isoformat()
    
    await _db.kb_articles.update_one(query, {"$set": update_data})
    return await _db.kb_articles.find_one({"id": article_id}, {"_id": 0})


@router.delete("/admin/articles/{article_id}")
async def delete_article(article_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a KB article"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": article_id}
    query = scope_query(query, org_id)
    
    await _db.kb_articles.update_one(query, {"$set": {"is_deleted": True}})
    return {"success": True}


@router.post("/admin/articles/{article_id}/publish")
async def publish_article(article_id: str, admin: dict = Depends(get_current_admin)):
    """Publish a draft article"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": article_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    result = await _db.kb_articles.update_one(
        query,
        {"$set": {
            "status": "published",
            "published_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"success": True}


@router.post("/admin/articles/{article_id}/unpublish")
async def unpublish_article(article_id: str, admin: dict = Depends(get_current_admin)):
    """Unpublish an article (back to draft)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": article_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    result = await _db.kb_articles.update_one(
        query,
        {"$set": {
            "status": "draft",
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"success": True}


# Need to import uuid at the top
import uuid
