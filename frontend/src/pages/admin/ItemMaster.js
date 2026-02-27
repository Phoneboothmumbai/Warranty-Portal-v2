import { useState, useEffect, useCallback } from 'react';
import {
  Plus, Search, Edit2, Trash2, MoreVertical, Package, Tag,
  Layers, Link2, IndianRupee, ChevronRight, X, ArrowLeft, Filter
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api/admin/item-master`;
const GST_SLABS = [0, 5, 12, 18, 28];

const headers = (token) => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' });

// ── Categories Tab ──────────────────────────────────────

function CategoriesTab({ token }) {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', description: '', sort_order: 0 });

  const fetch_ = useCallback(async () => {
    try {
      const res = await fetch(`${API}/categories`, { headers: headers(token) });
      const data = await res.json();
      setCategories(data.categories || []);
    } catch { toast.error('Failed to load categories'); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { fetch_(); }, [fetch_]);

  const openCreate = () => { setEditing(null); setForm({ name: '', description: '', sort_order: categories.length }); setModalOpen(true); };
  const openEdit = (c) => { setEditing(c); setForm({ name: c.name, description: c.description || '', sort_order: c.sort_order || 0 }); setModalOpen(true); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { toast.error('Name is required'); return; }
    try {
      const url = editing ? `${API}/categories/${editing.id}` : `${API}/categories`;
      const method = editing ? 'PUT' : 'POST';
      const res = await fetch(url, { method, headers: headers(token), body: JSON.stringify(form) });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed'); }
      toast.success(editing ? 'Category updated' : 'Category created');
      setModalOpen(false); fetch_();
    } catch (err) { toast.error(err.message); }
  };

  const handleDelete = async (c) => {
    if (!window.confirm(`Delete category "${c.name}"?`)) return;
    try {
      const res = await fetch(`${API}/categories/${c.id}`, { method: 'DELETE', headers: headers(token) });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed'); }
      toast.success('Category deleted'); fetch_();
    } catch (err) { toast.error(err.message); }
  };

  if (loading) return <div className="flex justify-center py-16"><div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-slate-500">{categories.length} categor{categories.length === 1 ? 'y' : 'ies'}</p>
        <Button onClick={openCreate} className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="add-category-btn">
          <Plus className="h-4 w-4 mr-2" />Add Category
        </Button>
      </div>

      {categories.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border border-slate-100">
          <Layers className="h-12 w-12 mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500 mb-4">No categories yet</p>
          <Button onClick={openCreate} variant="outline"><Plus className="h-4 w-4 mr-2" />Create your first category</Button>
        </div>
      ) : (
        <div className="grid gap-3">
          {categories.map(c => (
            <div key={c.id} className="bg-white rounded-xl border border-slate-100 px-5 py-4 flex items-center justify-between hover:border-slate-200 transition-colors" data-testid={`category-row-${c.id}`}>
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-[#E8F0FE] flex items-center justify-center">
                  <Layers className="h-5 w-5 text-[#0F62FE]" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">{c.name}</p>
                  {c.description && <p className="text-sm text-slate-500 mt-0.5">{c.description}</p>}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">{c.is_active !== false ? 'Active' : 'Inactive'}</Badge>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild><Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button></DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => openEdit(c)}><Edit2 className="h-4 w-4 mr-2" />Edit</DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleDelete(c)} className="text-red-600"><Trash2 className="h-4 w-4 mr-2" />Delete</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>{editing ? 'Edit' : 'New'} Category</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Name *</label>
              <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g., Security" data-testid="category-name-input" />
            </div>
            <div>
              <label className="form-label">Description</label>
              <input className="form-input" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Optional description" />
            </div>
            <div>
              <label className="form-label">Sort Order</label>
              <input type="number" className="form-input" value={form.sort_order} onChange={e => setForm({ ...form, sort_order: parseInt(e.target.value) || 0 })} min="0" />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="category-submit-btn">{editing ? 'Update' : 'Create'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Products Tab ────────────────────────────────────────

function ProductsTab({ token }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQ, setSearchQ] = useState('');
  const [filterCat, setFilterCat] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    category_id: '', name: '', sku: '', part_number: '', brand: '', manufacturer: '',
    description: '', unit_price: 0, gst_slab: 18, hsn_code: '', unit_of_measure: 'unit',
  });

  const fetchProducts = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filterCat) params.set('category_id', filterCat);
      if (searchQ) params.set('search', searchQ);
      const res = await fetch(`${API}/products?${params}`, { headers: headers(token) });
      const data = await res.json();
      setProducts(data.products || []);
    } catch { toast.error('Failed to load products'); }
    finally { setLoading(false); }
  }, [token, filterCat, searchQ]);

  const fetchCategories = useCallback(async () => {
    try {
      const res = await fetch(`${API}/categories`, { headers: headers(token) });
      const data = await res.json();
      setCategories(data.categories || []);
    } catch {}
  }, [token]);

  useEffect(() => { fetchCategories(); }, [fetchCategories]);
  useEffect(() => { setLoading(true); fetchProducts(); }, [fetchProducts]);

  const openCreate = () => {
    setEditing(null);
    setForm({ category_id: categories[0]?.id || '', name: '', sku: '', part_number: '', brand: '', manufacturer: '', description: '', unit_price: 0, gst_slab: 18, hsn_code: '', unit_of_measure: 'unit' });
    setModalOpen(true);
  };
  const openEdit = (p) => {
    setEditing(p);
    setForm({
      category_id: p.category_id || '', name: p.name, sku: p.sku || '', part_number: p.part_number || '',
      brand: p.brand || '', manufacturer: p.manufacturer || '', description: p.description || '',
      unit_price: p.unit_price || 0, gst_slab: p.gst_slab ?? 18, hsn_code: p.hsn_code || '', unit_of_measure: p.unit_of_measure || 'unit',
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { toast.error('Product name is required'); return; }
    if (!form.category_id) { toast.error('Category is required'); return; }
    try {
      const payload = { ...form, unit_price: parseFloat(form.unit_price) || 0, gst_slab: parseInt(form.gst_slab) };
      const url = editing ? `${API}/products/${editing.id}` : `${API}/products`;
      const method = editing ? 'PUT' : 'POST';
      const res = await fetch(url, { method, headers: headers(token), body: JSON.stringify(payload) });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed'); }
      toast.success(editing ? 'Product updated' : 'Product created');
      setModalOpen(false); fetchProducts();
    } catch (err) { toast.error(err.message); }
  };

  const handleDelete = async (p) => {
    if (!window.confirm(`Delete product "${p.name}"?`)) return;
    try {
      const res = await fetch(`${API}/products/${p.id}`, { method: 'DELETE', headers: headers(token) });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed'); }
      toast.success('Product deleted'); fetchProducts();
    } catch (err) { toast.error(err.message); }
  };

  const calcGst = (price, slab) => { const p = parseFloat(price) || 0; const g = parseInt(slab) || 0; return { gst: (p * g / 100).toFixed(2), total: (p + p * g / 100).toFixed(2) }; };

  return (
    <>
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-3 flex-1 w-full sm:w-auto">
          <div className="relative flex-1 sm:flex-initial">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input className="form-input pl-9 w-full sm:w-64" placeholder="Search products..." value={searchQ} onChange={e => setSearchQ(e.target.value)} data-testid="product-search-input" />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <select className="form-input pl-9 pr-8 appearance-none" value={filterCat} onChange={e => setFilterCat(e.target.value)} data-testid="product-category-filter">
              <option value="">All Categories</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
        </div>
        <Button onClick={openCreate} className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="add-product-btn">
          <Plus className="h-4 w-4 mr-2" />Add Product
        </Button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin" /></div>
        ) : products.length === 0 ? (
          <div className="text-center py-20">
            <Package className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No products found</p>
            <Button onClick={openCreate} variant="outline"><Plus className="h-4 w-4 mr-2" />Add your first product</Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-modern">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>SKU / Part #</th>
                  <th>Brand</th>
                  <th className="text-right">Price</th>
                  <th className="text-right">GST</th>
                  <th className="text-right">Total</th>
                  <th className="w-12"></th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => {
                  const { gst, total } = calcGst(p.unit_price, p.gst_slab);
                  return (
                    <tr key={p.id} data-testid={`product-row-${p.id}`}>
                      <td>
                        <p className="font-medium text-slate-900">{p.name}</p>
                        {p.description && <p className="text-xs text-slate-400 mt-0.5 max-w-[200px] truncate">{p.description}</p>}
                      </td>
                      <td><Badge variant="outline" className="text-xs">{p.category_name || '-'}</Badge></td>
                      <td>
                        <div className="space-y-0.5">
                          {p.sku && <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded font-mono block">{p.sku}</code>}
                          {p.part_number && <code className="text-xs bg-slate-50 px-1.5 py-0.5 rounded font-mono text-slate-500 block">{p.part_number}</code>}
                          {!p.sku && !p.part_number && <span className="text-slate-400">-</span>}
                        </div>
                      </td>
                      <td className="text-sm text-slate-600">{p.brand || p.manufacturer || '-'}</td>
                      <td className="text-right font-mono text-sm">₹{(p.unit_price || 0).toLocaleString('en-IN')}</td>
                      <td className="text-right"><Badge variant="secondary" className="text-xs font-mono">{p.gst_slab ?? 18}%</Badge></td>
                      <td className="text-right font-mono text-sm font-medium text-slate-900">₹{parseFloat(total).toLocaleString('en-IN')}</td>
                      <td>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild><Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button></DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEdit(p)}><Edit2 className="h-4 w-4 mr-2" />Edit</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleDelete(p)} className="text-red-600"><Trash2 className="h-4 w-4 mr-2" />Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <p className="text-sm text-slate-500 mt-3">{products.length} product{products.length !== 1 ? 's' : ''}</p>

      {/* Product Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>{editing ? 'Edit' : 'New'} Product</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Category *</label>
              <select className="form-input" value={form.category_id} onChange={e => setForm({ ...form, category_id: e.target.value })} data-testid="product-category-select">
                <option value="">Select category</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Product Name *</label>
              <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g., Hikvision 2MP Dome Camera" data-testid="product-name-input" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">SKU</label>
                <input className="form-input font-mono" value={form.sku} onChange={e => setForm({ ...form, sku: e.target.value })} placeholder="SKU-001" />
              </div>
              <div>
                <label className="form-label">Part Number</label>
                <input className="form-input font-mono" value={form.part_number} onChange={e => setForm({ ...form, part_number: e.target.value })} placeholder="DS-2CD1123G0E" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Brand</label>
                <input className="form-input" value={form.brand} onChange={e => setForm({ ...form, brand: e.target.value })} placeholder="Hikvision" />
              </div>
              <div>
                <label className="form-label">Manufacturer</label>
                <input className="form-input" value={form.manufacturer} onChange={e => setForm({ ...form, manufacturer: e.target.value })} placeholder="Hikvision India" />
              </div>
            </div>
            <div>
              <label className="form-label">Description</label>
              <textarea className="form-input min-h-[60px]" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Product details..." rows={2} />
            </div>

            {/* Pricing section */}
            <div className="border-t border-slate-100 pt-4">
              <p className="text-sm font-medium text-slate-700 mb-3 flex items-center gap-2"><IndianRupee className="h-4 w-4" /> Pricing & Tax</p>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="form-label">Unit Price (₹)</label>
                  <input type="number" step="0.01" className="form-input font-mono" value={form.unit_price} onChange={e => setForm({ ...form, unit_price: e.target.value })} min="0" data-testid="product-price-input" />
                </div>
                <div>
                  <label className="form-label">GST Slab</label>
                  <select className="form-input" value={form.gst_slab} onChange={e => setForm({ ...form, gst_slab: parseInt(e.target.value) })} data-testid="product-gst-select">
                    {GST_SLABS.map(s => <option key={s} value={s}>{s}%</option>)}
                  </select>
                </div>
                <div>
                  <label className="form-label">HSN Code</label>
                  <input className="form-input font-mono" value={form.hsn_code} onChange={e => setForm({ ...form, hsn_code: e.target.value })} placeholder="85258090" />
                </div>
              </div>
              {/* Live GST calc preview */}
              {parseFloat(form.unit_price) > 0 && (
                <div className="mt-3 p-3 bg-slate-50 rounded-lg text-sm grid grid-cols-3 gap-4">
                  <div>
                    <span className="text-slate-500">Base</span>
                    <p className="font-mono font-medium">₹{parseFloat(form.unit_price || 0).toLocaleString('en-IN')}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">GST ({form.gst_slab}%)</span>
                    <p className="font-mono font-medium">₹{calcGst(form.unit_price, form.gst_slab).gst}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Total</span>
                    <p className="font-mono font-semibold text-[#0F62FE]">₹{calcGst(form.unit_price, form.gst_slab).total}</p>
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className="form-label">Unit of Measure</label>
              <select className="form-input" value={form.unit_of_measure} onChange={e => setForm({ ...form, unit_of_measure: e.target.value })}>
                {['unit', 'piece', 'set', 'box', 'meter', 'kg', 'liter', 'pair'].map(u => <option key={u} value={u}>{u.charAt(0).toUpperCase() + u.slice(1)}</option>)}
              </select>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="product-submit-btn">{editing ? 'Update' : 'Create'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Bundles Tab ──────────────────────────────────────────

function BundlesTab({ token }) {
  const [bundles, setBundles] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ source_product_id: '', recommended_product_ids: [], description: '' });

  const fetchBundles = useCallback(async () => {
    try {
      const res = await fetch(`${API}/bundles`, { headers: headers(token) });
      const data = await res.json();
      setBundles(data.bundles || []);
    } catch { toast.error('Failed to load bundles'); }
    finally { setLoading(false); }
  }, [token]);

  const fetchProducts = useCallback(async () => {
    try {
      const res = await fetch(`${API}/products?limit=200`, { headers: headers(token) });
      const data = await res.json();
      setProducts(data.products || []);
    } catch {}
  }, [token]);

  useEffect(() => { fetchBundles(); fetchProducts(); }, [fetchBundles, fetchProducts]);

  const openCreate = () => {
    setEditing(null);
    setForm({ source_product_id: '', recommended_product_ids: [], description: '' });
    setModalOpen(true);
  };
  const openEdit = (b) => {
    setEditing(b);
    setForm({ source_product_id: b.source_product_id, recommended_product_ids: b.recommended_product_ids || [], description: b.description || '' });
    setModalOpen(true);
  };

  const toggleRecommended = (pid) => {
    setForm(prev => ({
      ...prev,
      recommended_product_ids: prev.recommended_product_ids.includes(pid)
        ? prev.recommended_product_ids.filter(id => id !== pid)
        : [...prev.recommended_product_ids, pid],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.source_product_id) { toast.error('Select a source product'); return; }
    if (form.recommended_product_ids.length === 0) { toast.error('Select at least one recommended product'); return; }
    try {
      const url = editing ? `${API}/bundles/${editing.id}` : `${API}/bundles`;
      const method = editing ? 'PUT' : 'POST';
      const payload = editing ? { recommended_product_ids: form.recommended_product_ids, description: form.description } : form;
      const res = await fetch(url, { method, headers: headers(token), body: JSON.stringify(payload) });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed'); }
      toast.success(editing ? 'Bundle updated' : 'Bundle created');
      setModalOpen(false); fetchBundles();
    } catch (err) { toast.error(err.message); }
  };

  const handleDelete = async (b) => {
    if (!window.confirm('Delete this bundle?')) return;
    try {
      const res = await fetch(`${API}/bundles/${b.id}`, { method: 'DELETE', headers: headers(token) });
      if (!res.ok) throw new Error('Failed');
      toast.success('Bundle deleted'); fetchBundles();
    } catch (err) { toast.error(err.message); }
  };

  // products available for recommendation (exclude source)
  const availableForRec = products.filter(p => p.id !== form.source_product_id);

  if (loading) return <div className="flex justify-center py-16"><div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-sm text-slate-500">{bundles.length} bundle{bundles.length !== 1 ? 's' : ''} configured</p>
          <p className="text-xs text-slate-400 mt-0.5">Bundles suggest related products during quotation creation</p>
        </div>
        <Button onClick={openCreate} className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="add-bundle-btn" disabled={products.length < 2}>
          <Plus className="h-4 w-4 mr-2" />Add Bundle
        </Button>
      </div>

      {bundles.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border border-slate-100">
          <Link2 className="h-12 w-12 mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500 mb-2">No bundles configured</p>
          <p className="text-sm text-slate-400 mb-4">Link related products so they're recommended together</p>
          {products.length >= 2 ? (
            <Button onClick={openCreate} variant="outline"><Plus className="h-4 w-4 mr-2" />Create your first bundle</Button>
          ) : (
            <p className="text-sm text-amber-600">Add at least 2 products first</p>
          )}
        </div>
      ) : (
        <div className="grid gap-4">
          {bundles.map(b => (
            <div key={b.id} className="bg-white rounded-xl border border-slate-100 p-5" data-testid={`bundle-row-${b.id}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center">
                      <Package className="h-4 w-4 text-amber-600" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{b.source_product?.name || 'Unknown product'}</p>
                      {b.source_product?.sku && <p className="text-xs text-slate-400 font-mono">{b.source_product.sku}</p>}
                    </div>
                  </div>
                  {b.description && <p className="text-sm text-slate-500 mb-3">{b.description}</p>}
                  <div className="flex items-center gap-2 mb-2">
                    <ChevronRight className="h-4 w-4 text-slate-400" />
                    <span className="text-xs text-slate-500 uppercase tracking-wide font-medium">Recommends</span>
                  </div>
                  <div className="flex flex-wrap gap-2 ml-6">
                    {(b.recommended_products || []).map(rp => (
                      <Badge key={rp.id} variant="secondary" className="text-xs py-1">
                        {rp.name}{rp.sku ? ` (${rp.sku})` : ''}
                      </Badge>
                    ))}
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild><Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button></DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => openEdit(b)}><Edit2 className="h-4 w-4 mr-2" />Edit</DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleDelete(b)} className="text-red-600"><Trash2 className="h-4 w-4 mr-2" />Delete</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Bundle Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>{editing ? 'Edit' : 'New'} Bundle</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            {!editing && (
              <div>
                <label className="form-label">Source Product *</label>
                <p className="text-xs text-slate-400 mb-1">When this product is added to a quotation...</p>
                <select className="form-input" value={form.source_product_id} onChange={e => setForm({ ...form, source_product_id: e.target.value, recommended_product_ids: form.recommended_product_ids.filter(id => id !== e.target.value) })} data-testid="bundle-source-select">
                  <option value="">Select product</option>
                  {products.map(p => <option key={p.id} value={p.id}>{p.name}{p.sku ? ` (${p.sku})` : ''}</option>)}
                </select>
              </div>
            )}
            <div>
              <label className="form-label">Recommended Products *</label>
              <p className="text-xs text-slate-400 mb-2">...these products will be suggested</p>
              {availableForRec.length === 0 ? (
                <p className="text-sm text-slate-400 py-4 text-center">No other products available</p>
              ) : (
                <div className="border border-slate-200 rounded-lg max-h-48 overflow-y-auto divide-y divide-slate-100">
                  {availableForRec.map(p => (
                    <label key={p.id} className="flex items-center gap-3 px-3 py-2.5 hover:bg-slate-50 cursor-pointer transition-colors">
                      <input
                        type="checkbox"
                        checked={form.recommended_product_ids.includes(p.id)}
                        onChange={() => toggleRecommended(p.id)}
                        className="rounded border-slate-300"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 truncate">{p.name}</p>
                        <p className="text-xs text-slate-400">{p.category_name}{p.sku ? ` / ${p.sku}` : ''}</p>
                      </div>
                      <span className="text-xs font-mono text-slate-500">₹{(p.unit_price || 0).toLocaleString('en-IN')}</span>
                    </label>
                  ))}
                </div>
              )}
              {form.recommended_product_ids.length > 0 && (
                <p className="text-xs text-slate-500 mt-2">{form.recommended_product_ids.length} selected</p>
              )}
            </div>
            <div>
              <label className="form-label">Description</label>
              <input className="form-input" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="e.g., Standard CCTV deployment kit" />
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="bundle-submit-btn">{editing ? 'Update' : 'Create'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Main Page ────────────────────────────────────────────

const TABS = [
  { key: 'categories', label: 'Categories', icon: Layers },
  { key: 'products', label: 'Products', icon: Package },
  { key: 'bundles', label: 'Bundles', icon: Link2 },
];

export default function ItemMaster() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('categories');

  return (
    <div className="space-y-6" data-testid="item-master-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Item Master</h1>
        <p className="text-slate-500 mt-1">Manage product categories, pricing with GST, and bundle recommendations</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white rounded-xl border border-slate-100 p-1 w-fit">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === t.key ? 'bg-[#0F62FE] text-white' : 'text-slate-600 hover:bg-slate-50'
            }`}
            data-testid={`tab-${t.key}`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'categories' && <CategoriesTab token={token} />}
      {activeTab === 'products' && <ProductsTab token={token} />}
      {activeTab === 'bundles' && <BundlesTab token={token} />}
    </div>
  );
}
