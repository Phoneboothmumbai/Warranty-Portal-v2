import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';
import { 
  FileText, Edit, Eye, EyeOff, Save, X, ExternalLink,
  Plus, Trash2, AlertCircle
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const DEFAULT_SLUGS = ['contact-us', 'privacy-policy', 'terms-of-service', 'refund-policy', 'disclaimer'];

export default function StaticPages() {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingPage, setEditingPage] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const token = localStorage.getItem('admin_token');

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      const response = await axios.get(`${API}/api/admin/pages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPages(response.data);
    } catch (error) {
      toast.error('Failed to fetch pages');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async (slug) => {
    try {
      const response = await axios.get(`${API}/api/admin/pages/${slug}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEditingPage(response.data);
    } catch (error) {
      toast.error('Failed to load page');
    }
  };

  const handleSave = async () => {
    try {
      await axios.put(`${API}/api/admin/pages/${editingPage.slug}`, {
        title: editingPage.title,
        content: editingPage.content,
        meta_title: editingPage.meta_title,
        meta_description: editingPage.meta_description,
        is_published: editingPage.is_published
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Page saved successfully');
      setEditingPage(null);
      fetchPages();
    } catch (error) {
      toast.error('Failed to save page');
    }
  };

  const togglePublish = async (slug, currentState) => {
    try {
      await axios.put(`${API}/api/admin/pages/${slug}`, {
        is_published: !currentState
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(currentState ? 'Page unpublished' : 'Page published');
      fetchPages();
    } catch (error) {
      toast.error('Failed to update page');
    }
  };

  const handleDelete = async (slug) => {
    if (!window.confirm('Are you sure you want to delete this page?')) return;
    
    try {
      await axios.delete(`${API}/api/admin/pages/${slug}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Page deleted');
      fetchPages();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete page');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto" data-testid="static-pages">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Static Pages</h1>
          <p className="text-slate-500">Manage legal pages, contact info, and other content</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Page
        </Button>
      </div>

      {/* Pages List */}
      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Page</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Slug</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Status</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Last Updated</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-slate-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {pages.map(page => (
                <tr key={page.slug} className="hover:bg-slate-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-50 rounded-lg">
                        <FileText className="w-4 h-4 text-blue-600" />
                      </div>
                      <span className="font-medium text-slate-900">{page.title}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <code className="px-2 py-1 bg-slate-100 rounded text-sm text-slate-600">
                      /page/{page.slug}
                    </code>
                  </td>
                  <td className="py-3 px-4">
                    <Badge variant={page.is_published ? 'default' : 'secondary'}>
                      {page.is_published ? 'Published' : 'Draft'}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-500">
                    {new Date(page.updated_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => window.open(`/page/${page.slug}`, '_blank')}
                        title="Preview"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => togglePublish(page.slug, page.is_published)}
                        title={page.is_published ? 'Unpublish' : 'Publish'}
                      >
                        {page.is_published ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(page.slug)}
                        title="Edit"
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      {!DEFAULT_SLUGS.includes(page.slug) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(page.slug)}
                          title="Delete"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Info Banner */}
      <div className="mt-4 flex items-start gap-3 p-4 bg-blue-50 rounded-lg border border-blue-100">
        <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <p className="font-medium mb-1">Page URLs</p>
          <p>Pages are accessible at <code className="bg-blue-100 px-1 rounded">/page/[slug]</code>. 
          Links are automatically added to the website footer.</p>
        </div>
      </div>

      {/* Edit Modal */}
      {editingPage && (
        <PageEditModal
          page={editingPage}
          onChange={setEditingPage}
          onSave={handleSave}
          onClose={() => setEditingPage(null)}
        />
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreatePageModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchPages();
          }}
          token={token}
        />
      )}
    </div>
  );
}

function PageEditModal({ page, onChange, onSave, onClose }) {
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave();
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold">Edit: {page.title}</h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
              <input
                type="text"
                value={page.title}
                onChange={(e) => onChange({ ...page, title: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Slug</label>
              <input
                type="text"
                value={page.slug}
                disabled
                className="w-full px-3 py-2 border rounded-lg bg-slate-50 text-slate-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Content (HTML)
            </label>
            <textarea
              value={page.content}
              onChange={(e) => onChange({ ...page, content: e.target.value })}
              rows={15}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              placeholder="<div>Your content here...</div>"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Meta Title (SEO)</label>
              <input
                type="text"
                value={page.meta_title || ''}
                onChange={(e) => onChange({ ...page, meta_title: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Optional SEO title"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Meta Description</label>
              <input
                type="text"
                value={page.meta_description || ''}
                onChange={(e) => onChange({ ...page, meta_description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Optional SEO description"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_published"
              checked={page.is_published}
              onChange={(e) => onChange({ ...page, is_published: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <label htmlFor="is_published" className="text-sm text-slate-700">
              Published (visible on website)
            </label>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t bg-slate-50">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

function CreatePageModal({ onClose, onSuccess, token }) {
  const [formData, setFormData] = useState({
    title: '',
    slug: '',
    content: '<div>\n  <h2>Your Page Title</h2>\n  <p>Your content here...</p>\n</div>',
    is_published: true
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.slug) {
      toast.error('Title and slug are required');
      return;
    }

    // Validate slug format
    if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      toast.error('Slug can only contain lowercase letters, numbers, and hyphens');
      return;
    }

    setSaving(true);
    try {
      await axios.post(`${API}/api/admin/pages`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Page created successfully');
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create page');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-lg">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold">Create New Page</h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="About Us"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Slug (URL)</label>
            <div className="flex items-center">
              <span className="px-3 py-2 bg-slate-100 border border-r-0 rounded-l-lg text-slate-500 text-sm">
                /page/
              </span>
              <input
                type="text"
                value={formData.slug}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '') 
                })}
                className="flex-1 px-3 py-2 border rounded-r-lg focus:ring-2 focus:ring-blue-500"
                placeholder="about-us"
                required
              />
            </div>
            <p className="text-xs text-slate-500 mt-1">Lowercase letters, numbers, and hyphens only</p>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="create_published"
              checked={formData.is_published}
              onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <label htmlFor="create_published" className="text-sm text-slate-700">
              Publish immediately
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="flex-1">
              {saving ? 'Creating...' : 'Create Page'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
