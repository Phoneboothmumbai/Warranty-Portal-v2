"""
Knowledge Base Models
=====================
Models for knowledge base articles and categories
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class KBCategory(BaseModel):
    """Knowledge Base Category"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    order: int = 0
    is_public: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: Optional[str] = None
    is_deleted: bool = False


class KBArticle(BaseModel):
    """Knowledge Base Article"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    category_id: Optional[str] = None
    title: str
    slug: str
    content: str  # HTML content
    excerpt: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: str = "draft"  # draft, published, archived
    is_featured: bool = False
    is_public: bool = True  # If false, only logged-in users can view
    views: int = 0
    helpful_yes: int = 0
    helpful_no: int = 0
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: Optional[str] = None
    published_at: Optional[str] = None
    is_deleted: bool = False


class KBCategoryCreate(BaseModel):
    """Create a KB category"""
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    order: int = 0
    is_public: bool = True


class KBCategoryUpdate(BaseModel):
    """Update a KB category"""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    order: Optional[int] = None
    is_public: Optional[bool] = None


class KBArticleCreate(BaseModel):
    """Create a KB article"""
    category_id: Optional[str] = None
    title: str
    slug: Optional[str] = None
    content: str
    excerpt: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: str = "draft"
    is_featured: bool = False
    is_public: bool = True


class KBArticleUpdate(BaseModel):
    """Update a KB article"""
    category_id: Optional[str] = None
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None
    is_public: Optional[bool] = None
