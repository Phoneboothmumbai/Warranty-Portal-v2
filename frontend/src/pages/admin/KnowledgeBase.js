import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { toast } from 'sonner';
import { 
  BookOpen, Plus, Edit, Trash2, Eye, Search, FolderOpen,
  FileText, Star, Globe, Lock, Loader2, CheckCircle, X,
  ThumbsUp, ThumbsDown
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function KnowledgeBase() {
  const [categories, setCategories] = useState([]);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('articles');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Modal states
  const [showArticleModal, setShowArticleModal] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [editingArticle, setEditingArticle] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  
  // Form states
  const [articleForm, setArticleForm] = useState({
    title: '',
    content: '',
    excerpt: '',
    category_id: '',
    tags: '',
    status: 'draft',
    is_featured: false,
    is_public: true
  });
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    description: '',
    icon: '',
    order: 0,
    is_public: true
  });
  
  const [saving, setSaving] = useState(false);
  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchCategories();
    fetchArticles();
  }, [selectedCategory, statusFilter, searchQuery]);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/api/kb/admin/categories`, { headers });
      setCategories(res.data);
    } catch (error) {
      toast.error('Failed to load categories');
    }
  };

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category_id', selectedCategory);
      if (statusFilter) params.append('status', statusFilter);
      if (searchQuery) params.append('search', searchQuery);
      
      const res = await axios.get(`${API}/api/kb/admin/articles?${params}`, { headers });
      setArticles(res.data.articles);
    } catch (error) {
      toast.error('Failed to load articles');
    } finally {
      setLoading(false);
    }
  };

  const openArticleModal = (article = null) => {
    if (article) {
      setEditingArticle(article);
      // Fetch full article with content
      axios.get(`${API}/api/kb/admin/articles/${article.id}`, { headers })
        .then(res => {
          setArticleForm({
            title: res.data.title,
            content: res.data.content,
            excerpt: res.data.excerpt || '',
            category_id: res.data.category_id || '',
            tags: res.data.tags?.join(', ') || '',
            status: res.data.status,
            is_featured: res.data.is_featured,
            is_public: res.data.is_public
          });
        });
    } else {
      setEditingArticle(null);
      setArticleForm({
        title: '',
        content: '',
        excerpt: '',
        category_id: '',
        tags: '',
        status: 'draft',
        is_featured: false,
        is_public: true
      });
    }
    setShowArticleModal(true);
  };

  const openCategoryModal = (category = null) => {
    if (category) {
      setEditingCategory(category);
      setCategoryForm({
        name: category.name,
        description: category.description || '',
        icon: category.icon || '',
        order: category.order,
        is_public: category.is_public
      });
    } else {
      setEditingCategory(null);
      setCategoryForm({
        name: '',
        description: '',
        icon: '',
        order: 0,
        is_public: true
      });
    }
    setShowCategoryModal(true);
  };

  const saveArticle = async () => {
    if (!articleForm.title || !articleForm.content) {
      toast.error('Title and content are required');
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        ...articleForm,
        tags: articleForm.tags ? articleForm.tags.split(',').map(t => t.trim()).filter(Boolean) : []
      };
      
      if (editingArticle) {
        await axios.put(`${API}/api/kb/admin/articles/${editingArticle.id}`, payload, { headers });
        toast.success('Article updated');
      } else {
        await axios.post(`${API}/api/kb/admin/articles`, payload, { headers });
        toast.success('Article created');
      }
      
      setShowArticleModal(false);
      fetchArticles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save article');
    } finally {
      setSaving(false);
    }
  };

  const saveCategory = async () => {
    if (!categoryForm.name) {
      toast.error('Category name is required');
      return;
    }
    
    setSaving(true);
    try {
      if (editingCategory) {
        await axios.put(`${API}/api/kb/admin/categories/${editingCategory.id}`, categoryForm, { headers });
        toast.success('Category updated');
      } else {
        await axios.post(`${API}/api/kb/admin/categories`, categoryForm, { headers });
        toast.success('Category created');
      }
      
      setShowCategoryModal(false);
      fetchCategories();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save category');
    } finally {
      setSaving(false);
    }
  };

  const deleteArticle = async (id) => {
    if (!window.confirm('Are you sure you want to delete this article?')) return;
    
    try {
      await axios.delete(`${API}/api/kb/admin/articles/${id}`, { headers });
      toast.success('Article deleted');
      fetchArticles();
    } catch (error) {
      toast.error('Failed to delete article');
    }
  };

  const deleteCategory = async (id) => {
    if (!window.confirm('Are you sure? Articles in this category will become uncategorized.')) return;
    
    try {
      await axios.delete(`${API}/api/kb/admin/categories/${id}`, { headers });
      toast.success('Category deleted');
      fetchCategories();
    } catch (error) {
      toast.error('Failed to delete category');
    }
  };

  const togglePublish = async (article) => {
    try {
      const endpoint = article.status === 'published' ? 'unpublish' : 'publish';
      await axios.post(`${API}/api/kb/admin/articles/${article.id}/${endpoint}`, {}, { headers });
      toast.success(article.status === 'published' ? 'Article unpublished' : 'Article published');
      fetchArticles();
    } catch (error) {
      toast.error('Failed to update article status');
    }
  };

  return (
    <div className="p-6" data-testid="knowledge-base">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-6 h-6" />
            Knowledge Base
          </h1>
          <p className="text-slate-500">Create and manage help articles for your clients</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => openCategoryModal()}>
            <FolderOpen className="w-4 h-4 mr-2" />
            New Category
          </Button>
          <Button onClick={() => openArticleModal()}>
            <Plus className="w-4 h-4 mr-2" />
            New Article
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        <button
          onClick={() => setActiveTab('articles')}
          className={`px-4 py-3 text-sm font-medium border-b-2 ${
            activeTab === 'articles' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'
          }`}
        >
          Articles ({articles.length})
        </button>
        <button
          onClick={() => setActiveTab('categories')}
          className={`px-4 py-3 text-sm font-medium border-b-2 ${
            activeTab === 'categories' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'
          }`}
        >
          Categories ({categories.length})
        </button>
      </div>

      {/* Articles Tab */}
      {activeTab === 'articles' && (
        <>
          {/* Filters */}
          <div className="flex gap-4 mb-6">
            <div className="flex-1 max-w-sm">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Search articles..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={selectedCategory}
              onChange={e => setSelectedCategory(e.target.value)}
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
            >
              <option value="">All Status</option>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </div>

          {/* Articles List */}
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
          ) : articles.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <FileText className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                <h3 className="font-medium text-slate-900">No articles yet</h3>
                <p className="text-slate-500 mt-1">Create your first knowledge base article</p>
                <Button className="mt-4" onClick={() => openArticleModal()}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Article
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {articles.map(article => (
                <Card key={article.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium text-slate-900">{article.title}</h3>
                          {article.is_featured && (
                            <Star className="w-4 h-4 text-amber-500 fill-amber-500" />
                          )}
                        </div>
                        <p className="text-sm text-slate-500 line-clamp-2">{article.excerpt}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                          <span>{article.category_name || 'Uncategorized'}</span>
                          <span>•</span>
                          <span>{article.views} views</span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <ThumbsUp className="w-3 h-3" /> {article.helpful_yes}
                          </span>
                          <span className="flex items-center gap-1">
                            <ThumbsDown className="w-3 h-3" /> {article.helpful_no}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Badge variant={article.status === 'published' ? 'default' : 'secondary'}>
                          {article.status}
                        </Badge>
                        {article.is_public ? (
                          <Globe className="w-4 h-4 text-slate-400" />
                        ) : (
                          <Lock className="w-4 h-4 text-slate-400" />
                        )}
                        <Button variant="ghost" size="sm" onClick={() => togglePublish(article)}>
                          {article.status === 'published' ? 'Unpublish' : 'Publish'}
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => openArticleModal(article)}>
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => deleteArticle(article.id)}>
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* Categories Tab */}
      {activeTab === 'categories' && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.length === 0 ? (
            <Card className="col-span-full">
              <CardContent className="py-12 text-center">
                <FolderOpen className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                <h3 className="font-medium text-slate-900">No categories yet</h3>
                <p className="text-slate-500 mt-1">Create categories to organize your articles</p>
                <Button className="mt-4" onClick={() => openCategoryModal()}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Category
                </Button>
              </CardContent>
            </Card>
          ) : (
            categories.map(category => (
              <Card key={category.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-medium text-slate-900">{category.name}</h3>
                      <p className="text-sm text-slate-500 mt-1">{category.description || 'No description'}</p>
                      <p className="text-xs text-slate-400 mt-2">{category.article_count} articles</p>
                    </div>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm" onClick={() => openCategoryModal(category)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteCategory(category.id)}>
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Article Modal */}
      {showArticleModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">
                {editingArticle ? 'Edit Article' : 'New Article'}
              </h2>
              <Button variant="ghost" size="sm" onClick={() => setShowArticleModal(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  value={articleForm.title}
                  onChange={e => setArticleForm({...articleForm, title: e.target.value})}
                  placeholder="Article title"
                />
              </div>
              <div>
                <Label htmlFor="category">Category</Label>
                <select
                  id="category"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  value={articleForm.category_id}
                  onChange={e => setArticleForm({...articleForm, category_id: e.target.value})}
                >
                  <option value="">Uncategorized</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="content">Content *</Label>
                <Textarea
                  id="content"
                  value={articleForm.content}
                  onChange={e => setArticleForm({...articleForm, content: e.target.value})}
                  placeholder="Write your article content (HTML supported)..."
                  rows={12}
                />
              </div>
              <div>
                <Label htmlFor="excerpt">Excerpt</Label>
                <Textarea
                  id="excerpt"
                  value={articleForm.excerpt}
                  onChange={e => setArticleForm({...articleForm, excerpt: e.target.value})}
                  placeholder="Brief summary (auto-generated if empty)"
                  rows={2}
                />
              </div>
              <div>
                <Label htmlFor="tags">Tags</Label>
                <Input
                  id="tags"
                  value={articleForm.tags}
                  onChange={e => setArticleForm({...articleForm, tags: e.target.value})}
                  placeholder="tag1, tag2, tag3"
                />
              </div>
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={articleForm.is_featured}
                    onChange={e => setArticleForm({...articleForm, is_featured: e.target.checked})}
                    className="rounded"
                  />
                  <span className="text-sm">Featured article</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={articleForm.is_public}
                    onChange={e => setArticleForm({...articleForm, is_public: e.target.checked})}
                    className="rounded"
                  />
                  <span className="text-sm">Publicly visible</span>
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-2 p-4 border-t">
              <Button variant="outline" onClick={() => setShowArticleModal(false)}>Cancel</Button>
              <Button onClick={saveArticle} disabled={saving}>
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                {editingArticle ? 'Update' : 'Create'} Article
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Category Modal */}
      {showCategoryModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">
                {editingCategory ? 'Edit Category' : 'New Category'}
              </h2>
              <Button variant="ghost" size="sm" onClick={() => setShowCategoryModal(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <Label htmlFor="cat-name">Name *</Label>
                <Input
                  id="cat-name"
                  value={categoryForm.name}
                  onChange={e => setCategoryForm({...categoryForm, name: e.target.value})}
                  placeholder="Category name"
                />
              </div>
              <div>
                <Label htmlFor="cat-desc">Description</Label>
                <Textarea
                  id="cat-desc"
                  value={categoryForm.description}
                  onChange={e => setCategoryForm({...categoryForm, description: e.target.value})}
                  placeholder="Brief description"
                  rows={2}
                />
              </div>
              <div>
                <Label htmlFor="cat-order">Display Order</Label>
                <Input
                  id="cat-order"
                  type="number"
                  value={categoryForm.order}
                  onChange={e => setCategoryForm({...categoryForm, order: parseInt(e.target.value)})}
                />
              </div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={categoryForm.is_public}
                  onChange={e => setCategoryForm({...categoryForm, is_public: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm">Publicly visible</span>
              </label>
            </div>
            <div className="flex justify-end gap-2 p-4 border-t">
              <Button variant="outline" onClick={() => setShowCategoryModal(false)}>Cancel</Button>
              <Button onClick={saveCategory} disabled={saving}>
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                {editingCategory ? 'Update' : 'Create'} Category
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
