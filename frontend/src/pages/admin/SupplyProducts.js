import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, Package, MoreVertical, FolderOpen, 
  CheckCircle, XCircle, Tag, Box, Upload, Image, IndianRupee
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { BulkImport } from '../../components/ui/bulk-import';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Bulk import configuration
const bulkImportColumns = [
  { key: 'name', label: 'Product Name', required: true, example: 'A4 Paper (500 sheets)' },
  { key: 'category', label: 'Category', required: true, example: 'Stationery' },
  { key: 'description', label: 'Description', required: false, example: 'High quality printing paper' },
  { key: 'unit', label: 'Unit', required: false, example: 'ream' },
  { key: 'price', label: 'Price', required: false, example: '250' },
  { key: 'sku', label: 'SKU', required: false, example: 'A4-500-WHT' },
  { key: 'internal_notes', label: 'Internal Notes', required: false, example: 'Vendor: XYZ, Cost: Rs 250' },
];

const productSampleData = [
  { name: 'A4 Paper (500 sheets)', category: 'Stationery', description: 'High quality printing paper', unit: 'ream', price: '250', sku: 'A4-500', internal_notes: 'Vendor: XYZ' },
  { name: 'Black Toner HP 26A', category: 'Printer Consumables', description: 'Compatible with HP LaserJet Pro', unit: 'cartridge', price: '3500', sku: 'HP-26A-BLK', internal_notes: 'High yield' },
];

const SupplyProducts = () => {
  const { token } = useAuth();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  
  // Product modal
  const [productModalOpen, setProductModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState({
    category_id: '',
    name: '',
    description: '',
    unit: 'piece',
    price: '',
    image_url: '',
    sku: '',
    internal_notes: ''
  });
  const [imageUploading, setImageUploading] = useState(false);

  // Category modal
  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    icon: '',
    description: '',
    sort_order: 0
  });

  const fetchData = useCallback(async () => {
    try {
      const [productsRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/admin/supply-products`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/supply-categories`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setProducts(productsRes.data);
      setCategories(categoriesRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Product handlers
  const openProductModal = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setProductForm({
        category_id: product.category_id,
        name: product.name,
        description: product.description || '',
        unit: product.unit || 'piece',
        internal_notes: product.internal_notes || ''
      });
    } else {
      setEditingProduct(null);
      setProductForm({
        category_id: categories[0]?.id || '',
        name: '',
        description: '',
        unit: 'piece',
        internal_notes: ''
      });
    }
    setProductModalOpen(true);
  };

  const handleProductSubmit = async (e) => {
    e.preventDefault();
    if (!productForm.category_id || !productForm.name) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      if (editingProduct) {
        await axios.put(`${API}/admin/supply-products/${editingProduct.id}`, productForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Product updated');
      } else {
        await axios.post(`${API}/admin/supply-products`, productForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Product created');
      }
      fetchData();
      setProductModalOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const deleteProduct = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    try {
      await axios.delete(`${API}/admin/supply-products/${productId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Product deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete product');
    }
  };

  const toggleProductStatus = async (product) => {
    try {
      await axios.put(`${API}/admin/supply-products/${product.id}`, 
        { is_active: !product.is_active },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Product ${product.is_active ? 'disabled' : 'enabled'}`);
      fetchData();
    } catch (error) {
      toast.error('Failed to update product');
    }
  };

  // Category handlers
  const openCategoryModal = (category = null) => {
    if (category) {
      setEditingCategory(category);
      setCategoryForm({
        name: category.name,
        icon: category.icon || '',
        description: category.description || '',
        sort_order: category.sort_order || 0
      });
    } else {
      setEditingCategory(null);
      setCategoryForm({
        name: '',
        icon: '',
        description: '',
        sort_order: categories.length
      });
    }
    setCategoryModalOpen(true);
  };

  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    if (!categoryForm.name) {
      toast.error('Please enter a category name');
      return;
    }

    try {
      if (editingCategory) {
        await axios.put(`${API}/admin/supply-categories/${editingCategory.id}`, categoryForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Category updated');
      } else {
        await axios.post(`${API}/admin/supply-categories`, categoryForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Category created');
      }
      fetchData();
      setCategoryModalOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const deleteCategory = async (categoryId) => {
    const productCount = products.filter(p => p.category_id === categoryId).length;
    if (productCount > 0) {
      toast.error(`Cannot delete category with ${productCount} products. Remove products first.`);
      return;
    }
    if (!window.confirm('Are you sure you want to delete this category?')) return;
    try {
      await axios.delete(`${API}/admin/supply-categories/${categoryId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Category deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete category');
    }
  };

  const handleBulkImport = async (records) => {
    const response = await axios.post(`${API}/admin/bulk-import/supply-products`, 
      { records },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    fetchData();
    return response.data;
  };

  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !filterCategory || product.category_id === filterCategory;
    return matchesSearch && matchesCategory;
  });

  const getCategoryName = (categoryId) => {
    return categories.find(c => c.id === categoryId)?.name || 'Unknown';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Office Supplies - Products</h1>
          <p className="text-slate-500 mt-1">Manage supply categories and products</p>
        </div>
        <div className="flex gap-2">
          <BulkImport
            entityName="Products"
            columns={bulkImportColumns}
            onImport={handleBulkImport}
            sampleData={productSampleData}
          />
          <Button variant="outline" onClick={() => openCategoryModal()} data-testid="add-category-btn">
            <FolderOpen className="h-4 w-4 mr-2" />
            Add Category
          </Button>
          <Button onClick={() => openProductModal()} className="bg-emerald-600 hover:bg-emerald-700" data-testid="add-product-btn">
            <Plus className="h-4 w-4 mr-2" />
            Add Product
          </Button>
        </div>
      </div>

      {/* Categories Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <FolderOpen className="h-4 w-4" />
          Categories ({categories.length})
        </h2>
        <div className="flex flex-wrap gap-2">
          {categories.map(category => (
            <div 
              key={category.id}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg group"
            >
              <span>{category.icon}</span>
              <span className="text-sm font-medium text-slate-700">{category.name}</span>
              <span className="text-xs text-slate-400">
                ({products.filter(p => p.category_id === category.id).length})
              </span>
              <div className="hidden group-hover:flex items-center gap-1 ml-1">
                <button 
                  onClick={() => openCategoryModal(category)}
                  className="p-1 hover:bg-slate-200 rounded"
                >
                  <Edit2 className="h-3 w-3 text-slate-500" />
                </button>
                <button 
                  onClick={() => deleteCategory(category.id)}
                  className="p-1 hover:bg-red-100 rounded"
                >
                  <Trash2 className="h-3 w-3 text-red-500" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">All Categories</option>
          {categories.map(cat => (
            <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
          ))}
        </select>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Product</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Category</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Unit</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredProducts.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                  <Package className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                  <p>No products found</p>
                </td>
              </tr>
            ) : (
              filteredProducts.map(product => (
                <tr key={product.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                        <Box className="h-5 w-5 text-slate-400" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{product.name}</p>
                        {product.description && (
                          <p className="text-sm text-slate-500">{product.description}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 bg-slate-100 rounded text-sm text-slate-700">
                      {product.category_name || getCategoryName(product.category_id)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-600">{product.unit}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      product.is_active 
                        ? 'bg-emerald-100 text-emerald-700' 
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                      {product.is_active ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                      {product.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openProductModal(product)}>
                          <Edit2 className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => toggleProductStatus(product)}>
                          {product.is_active ? (
                            <><XCircle className="h-4 w-4 mr-2" /> Disable</>
                          ) : (
                            <><CheckCircle className="h-4 w-4 mr-2" /> Enable</>
                          )}
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => deleteProduct(product.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Product Modal */}
      <Dialog open={productModalOpen} onOpenChange={setProductModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingProduct ? 'Edit Product' : 'Add Product'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleProductSubmit} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Category *</label>
              <select
                value={productForm.category_id}
                onChange={(e) => setProductForm({ ...productForm, category_id: e.target.value })}
                className="form-select"
                required
              >
                <option value="">Select category...</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="form-label">Product Name *</label>
              <input
                type="text"
                value={productForm.name}
                onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                className="form-input"
                placeholder="e.g., A4 Paper (500 sheets)"
                required
              />
            </div>
            <div>
              <label className="form-label">Description</label>
              <input
                type="text"
                value={productForm.description}
                onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                className="form-input"
                placeholder="Optional description"
              />
            </div>
            <div>
              <label className="form-label">Unit</label>
              <select
                value={productForm.unit}
                onChange={(e) => setProductForm({ ...productForm, unit: e.target.value })}
                className="form-select"
              >
                <option value="piece">Piece</option>
                <option value="pack">Pack</option>
                <option value="box">Box</option>
                <option value="ream">Ream</option>
                <option value="set">Set</option>
                <option value="cartridge">Cartridge</option>
                <option value="roll">Roll</option>
                <option value="bottle">Bottle</option>
                <option value="pack of 10">Pack of 10</option>
                <option value="pack of 50">Pack of 50</option>
                <option value="pack of 100">Pack of 100</option>
              </select>
            </div>
            <div>
              <label className="form-label">Internal Notes (Admin only)</label>
              <textarea
                value={productForm.internal_notes}
                onChange={(e) => setProductForm({ ...productForm, internal_notes: e.target.value })}
                className="form-input"
                rows={2}
                placeholder="Vendor info, cost, availability..."
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setProductModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700">
                {editingProduct ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Category Modal */}
      <Dialog open={categoryModalOpen} onOpenChange={setCategoryModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingCategory ? 'Edit Category' : 'Add Category'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCategorySubmit} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Category Name *</label>
              <input
                type="text"
                value={categoryForm.name}
                onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                className="form-input"
                placeholder="e.g., Stationery"
                required
              />
            </div>
            <div>
              <label className="form-label">Icon (Emoji)</label>
              <input
                type="text"
                value={categoryForm.icon}
                onChange={(e) => setCategoryForm({ ...categoryForm, icon: e.target.value })}
                className="form-input"
                placeholder="e.g., 📁 🖨 🔌"
              />
            </div>
            <div>
              <label className="form-label">Description</label>
              <input
                type="text"
                value={categoryForm.description}
                onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
                className="form-input"
                placeholder="Optional description"
              />
            </div>
            <div>
              <label className="form-label">Sort Order</label>
              <input
                type="number"
                value={categoryForm.sort_order}
                onChange={(e) => setCategoryForm({ ...categoryForm, sort_order: parseInt(e.target.value) || 0 })}
                className="form-input"
                min="0"
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setCategoryModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700">
                {editingCategory ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SupplyProducts;
