import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, Building2, Clock, 
  CheckCircle2, AlertTriangle, MoreVertical, RefreshCw,
  Timer, Calendar, Users, Shield
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function TicketingSettings() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('departments');
  const [loading, setLoading] = useState(true);
  
  // Data
  const [departments, setDepartments] = useState([]);
  const [slaPolicies, setSLAPolicies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [admins, setAdmins] = useState([]);
  
  // Modals
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showSLAModal, setShowSLAModal] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  // Department form
  const [deptForm, setDeptForm] = useState({
    name: '', description: '', email: '', default_priority: 'medium',
    default_sla_id: '', auto_assign_to: '', is_public: true, sort_order: 0
  });
  
  // SLA form
  const [slaForm, setSLAForm] = useState({
    name: '', description: '', response_time_hours: 4, resolution_time_hours: 24,
    response_time_business_hours: true, resolution_time_business_hours: true,
    business_hours_start: '09:00', business_hours_end: '18:00',
    business_days: [1, 2, 3, 4, 5], is_default: false
  });
  
  // Category form
  const [categoryForm, setCategoryForm] = useState({
    name: '', description: '', auto_department_id: '', auto_priority: '', sort_order: 0
  });

  const fetchData = useCallback(async () => {
    try {
      const [deptsRes, slasRes, catsRes, adminsRes] = await Promise.all([
        axios.get(`${API}/ticketing/admin/departments?include_inactive=true`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/ticketing/admin/sla-policies?include_inactive=true`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/ticketing/admin/categories`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/users`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setDepartments(deptsRes.data || []);
      setSLAPolicies(slasRes.data || []);
      setCategories(catsRes.data || []);
      setAdmins(adminsRes.data || []);
    } catch (error) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Department handlers
  const openDeptModal = (dept = null) => {
    if (dept) {
      setEditingItem(dept);
      setDeptForm({
        name: dept.name || '',
        description: dept.description || '',
        email: dept.email || '',
        default_priority: dept.default_priority || 'medium',
        default_sla_id: dept.default_sla_id || '',
        auto_assign_to: dept.auto_assign_to || '',
        is_public: dept.is_public !== false,
        sort_order: dept.sort_order || 0
      });
    } else {
      setEditingItem(null);
      setDeptForm({
        name: '', description: '', email: '', default_priority: 'medium',
        default_sla_id: '', auto_assign_to: '', is_public: true, sort_order: 0
      });
    }
    setShowDeptModal(true);
  };

  const saveDepartment = async () => {
    try {
      if (editingItem) {
        await axios.put(`${API}/ticketing/admin/departments/${editingItem.id}`, deptForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Department updated');
      } else {
        await axios.post(`${API}/ticketing/admin/departments`, deptForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Department created');
      }
      setShowDeptModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save department');
    }
  };

  const deleteDepartment = async (id) => {
    if (!window.confirm('Are you sure you want to delete this department?')) return;
    try {
      await axios.delete(`${API}/ticketing/admin/departments/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Department deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete department');
    }
  };

  // SLA handlers
  const openSLAModal = (sla = null) => {
    if (sla) {
      setEditingItem(sla);
      setSLAForm({
        name: sla.name || '',
        description: sla.description || '',
        response_time_hours: sla.response_time_hours || 4,
        resolution_time_hours: sla.resolution_time_hours || 24,
        response_time_business_hours: sla.response_time_business_hours !== false,
        resolution_time_business_hours: sla.resolution_time_business_hours !== false,
        business_hours_start: sla.business_hours_start || '09:00',
        business_hours_end: sla.business_hours_end || '18:00',
        business_days: sla.business_days || [1, 2, 3, 4, 5],
        is_default: sla.is_default || false
      });
    } else {
      setEditingItem(null);
      setSLAForm({
        name: '', description: '', response_time_hours: 4, resolution_time_hours: 24,
        response_time_business_hours: true, resolution_time_business_hours: true,
        business_hours_start: '09:00', business_hours_end: '18:00',
        business_days: [1, 2, 3, 4, 5], is_default: false
      });
    }
    setShowSLAModal(true);
  };

  const saveSLA = async () => {
    try {
      if (editingItem) {
        await axios.put(`${API}/ticketing/admin/sla-policies/${editingItem.id}`, slaForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('SLA Policy updated');
      } else {
        await axios.post(`${API}/ticketing/admin/sla-policies`, slaForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('SLA Policy created');
      }
      setShowSLAModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save SLA policy');
    }
  };

  const deleteSLA = async (id) => {
    if (!window.confirm('Are you sure you want to delete this SLA policy?')) return;
    try {
      await axios.delete(`${API}/ticketing/admin/sla-policies/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('SLA Policy deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete SLA policy');
    }
  };

  // Category handlers
  const openCategoryModal = (cat = null) => {
    if (cat) {
      setEditingItem(cat);
      setCategoryForm({
        name: cat.name || '',
        description: cat.description || '',
        auto_department_id: cat.auto_department_id || '',
        auto_priority: cat.auto_priority || '',
        sort_order: cat.sort_order || 0
      });
    } else {
      setEditingItem(null);
      setCategoryForm({ name: '', description: '', auto_department_id: '', auto_priority: '', sort_order: 0 });
    }
    setShowCategoryModal(true);
  };

  const saveCategory = async () => {
    try {
      if (editingItem) {
        await axios.put(`${API}/ticketing/admin/categories/${editingItem.id}`, categoryForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Category updated');
      } else {
        await axios.post(`${API}/ticketing/admin/categories`, categoryForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Category created');
      }
      setShowCategoryModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save category');
    }
  };

  const deleteCategory = async (id) => {
    if (!window.confirm('Are you sure you want to delete this category?')) return;
    try {
      await axios.delete(`${API}/ticketing/admin/categories/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Category deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete category');
    }
  };

  const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div data-testid="ticketing-settings-page" className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Ticketing Configuration</h1>
        <p className="text-slate-500 text-sm">Manage departments, SLA policies, and categories</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 pb-2">
        {[
          { key: 'departments', label: 'Departments', icon: Building2, count: departments.length },
          { key: 'sla', label: 'SLA Policies', icon: Timer, count: slaPolicies.length },
          { key: 'categories', label: 'Categories', icon: Shield, count: categories.length }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-white border border-b-white border-slate-200 -mb-[1px] text-slate-900'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
            <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">{tab.count}</span>
          </button>
        ))}
      </div>

      {/* Departments Tab */}
      {activeTab === 'departments' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-600">Organize tickets by department for better routing and management</p>
            <Button onClick={() => openDeptModal()}>
              <Plus className="h-4 w-4 mr-2" />
              Add Department
            </Button>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Name</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Default SLA</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Default Priority</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Auto Assign</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Public</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {departments.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-slate-500">
                      No departments configured. Create one to get started.
                    </td>
                  </tr>
                ) : (
                  departments.map(dept => (
                    <tr key={dept.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium text-slate-900">{dept.name}</p>
                          {dept.description && <p className="text-xs text-slate-500">{dept.description}</p>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">
                        {slaPolicies.find(s => s.id === dept.default_sla_id)?.name || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                          dept.default_priority === 'critical' ? 'bg-red-100 text-red-700' :
                          dept.default_priority === 'high' ? 'bg-orange-100 text-orange-700' :
                          dept.default_priority === 'medium' ? 'bg-blue-100 text-blue-700' :
                          'bg-slate-100 text-slate-600'
                        }`}>
                          {dept.default_priority}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">
                        {admins.find(a => a.id === dept.auto_assign_to)?.name || '-'}
                      </td>
                      <td className="px-4 py-3">
                        {dept.is_public ? (
                          <span className="text-emerald-600">✓</span>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm"><MoreVertical className="h-4 w-4" /></Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openDeptModal(dept)}>
                              <Edit2 className="h-4 w-4 mr-2" /> Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => deleteDepartment(dept.id)} className="text-red-600">
                              <Trash2 className="h-4 w-4 mr-2" /> Delete
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
        </div>
      )}

      {/* SLA Policies Tab */}
      {activeTab === 'sla' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-600">Define service level agreements for response and resolution times</p>
            <Button onClick={() => openSLAModal()}>
              <Plus className="h-4 w-4 mr-2" />
              Add SLA Policy
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {slaPolicies.length === 0 ? (
              <div className="col-span-full bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
                No SLA policies configured. Create one to get started.
              </div>
            ) : (
              slaPolicies.map(sla => (
                <div key={sla.id} className={`bg-white rounded-xl border p-4 ${sla.is_default ? 'border-blue-300 ring-1 ring-blue-100' : 'border-slate-200'}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-slate-900">{sla.name}</h3>
                        {sla.is_default && (
                          <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">Default</span>
                        )}
                      </div>
                      {sla.description && <p className="text-xs text-slate-500 mt-1">{sla.description}</p>}
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm"><MoreVertical className="h-4 w-4" /></Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openSLAModal(sla)}>
                          <Edit2 className="h-4 w-4 mr-2" /> Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => deleteSLA(sla.id)} className="text-red-600">
                          <Trash2 className="h-4 w-4 mr-2" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Response Time</span>
                      <span className="font-medium text-slate-900">{sla.response_time_hours}h</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Resolution Time</span>
                      <span className="font-medium text-slate-900">{sla.resolution_time_hours}h</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Business Hours</span>
                      <span className="text-slate-700">{sla.business_hours_start} - {sla.business_hours_end}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Categories Tab */}
      {activeTab === 'categories' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-600">Categorize tickets for better organization and auto-routing</p>
            <Button onClick={() => openCategoryModal()}>
              <Plus className="h-4 w-4 mr-2" />
              Add Category
            </Button>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Name</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Auto Department</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Auto Priority</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {categories.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-12 text-center text-slate-500">
                      No categories configured. Create one to get started.
                    </td>
                  </tr>
                ) : (
                  categories.map(cat => (
                    <tr key={cat.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <p className="font-medium text-slate-900">{cat.name}</p>
                        {cat.description && <p className="text-xs text-slate-500">{cat.description}</p>}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">
                        {departments.find(d => d.id === cat.auto_department_id)?.name || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600 capitalize">
                        {cat.auto_priority || '-'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm"><MoreVertical className="h-4 w-4" /></Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openCategoryModal(cat)}>
                              <Edit2 className="h-4 w-4 mr-2" /> Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => deleteCategory(cat.id)} className="text-red-600">
                              <Trash2 className="h-4 w-4 mr-2" /> Delete
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
        </div>
      )}

      {/* Department Modal */}
      <Dialog open={showDeptModal} onOpenChange={setShowDeptModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Department' : 'Add Department'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Name *</label>
              <input
                type="text"
                value={deptForm.name}
                onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="e.g., IT Support"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Description</label>
              <input
                type="text"
                value={deptForm.description}
                onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="Brief description"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Default SLA</label>
                <select
                  value={deptForm.default_sla_id}
                  onChange={(e) => setDeptForm({ ...deptForm, default_sla_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="">None</option>
                  {slaPolicies.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Default Priority</label>
                <select
                  value={deptForm.default_priority}
                  onChange={(e) => setDeptForm({ ...deptForm, default_priority: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Auto Assign To</label>
              <select
                value={deptForm.auto_assign_to}
                onChange={(e) => setDeptForm({ ...deptForm, auto_assign_to: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              >
                <option value="">No auto-assignment</option>
                {admins.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={deptForm.is_public}
                onChange={(e) => setDeptForm({ ...deptForm, is_public: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm text-slate-700">Visible to customers in portal</span>
            </label>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => setShowDeptModal(false)}>Cancel</Button>
              <Button onClick={saveDepartment}>{editingItem ? 'Update' : 'Create'}</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* SLA Modal */}
      <Dialog open={showSLAModal} onOpenChange={setShowSLAModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit SLA Policy' : 'Add SLA Policy'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Name *</label>
              <input
                type="text"
                value={slaForm.name}
                onChange={(e) => setSLAForm({ ...slaForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="e.g., Standard SLA"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Description</label>
              <input
                type="text"
                value={slaForm.description}
                onChange={(e) => setSLAForm({ ...slaForm, description: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="Brief description"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Response Time (hours)</label>
                <input
                  type="number"
                  min="1"
                  value={slaForm.response_time_hours}
                  onChange={(e) => setSLAForm({ ...slaForm, response_time_hours: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Resolution Time (hours)</label>
                <input
                  type="number"
                  min="1"
                  value={slaForm.resolution_time_hours}
                  onChange={(e) => setSLAForm({ ...slaForm, resolution_time_hours: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Business Hours Start</label>
                <input
                  type="time"
                  value={slaForm.business_hours_start}
                  onChange={(e) => setSLAForm({ ...slaForm, business_hours_start: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Business Hours End</label>
                <input
                  type="time"
                  value={slaForm.business_hours_end}
                  onChange={(e) => setSLAForm({ ...slaForm, business_hours_end: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-2">Business Days</label>
              <div className="flex gap-2">
                {DAYS.map((day, i) => (
                  <button
                    key={day}
                    type="button"
                    onClick={() => {
                      const days = slaForm.business_days.includes(i)
                        ? slaForm.business_days.filter(d => d !== i)
                        : [...slaForm.business_days, i];
                      setSLAForm({ ...slaForm, business_days: days });
                    }}
                    className={`px-3 py-1 rounded text-sm ${
                      slaForm.business_days.includes(i)
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {day}
                  </button>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={slaForm.is_default}
                onChange={(e) => setSLAForm({ ...slaForm, is_default: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm text-slate-700">Set as default SLA policy</span>
            </label>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => setShowSLAModal(false)}>Cancel</Button>
              <Button onClick={saveSLA}>{editingItem ? 'Update' : 'Create'}</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Category Modal */}
      <Dialog open={showCategoryModal} onOpenChange={setShowCategoryModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Category' : 'Add Category'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Name *</label>
              <input
                type="text"
                value={categoryForm.name}
                onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="e.g., Hardware Issue"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Description</label>
              <input
                type="text"
                value={categoryForm.description}
                onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Auto-route to Department</label>
                <select
                  value={categoryForm.auto_department_id}
                  onChange={(e) => setCategoryForm({ ...categoryForm, auto_department_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="">No auto-routing</option>
                  {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Auto Priority</label>
                <select
                  value={categoryForm.auto_priority}
                  onChange={(e) => setCategoryForm({ ...categoryForm, auto_priority: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="">No auto-priority</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => setShowCategoryModal(false)}>Cancel</Button>
              <Button onClick={saveCategory}>{editingItem ? 'Update' : 'Create'}</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
