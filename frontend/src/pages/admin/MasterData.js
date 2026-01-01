import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, Settings2, X, MoreVertical, 
  Laptop, Wrench, Activity, CheckCircle, Tag, RefreshCw,
  ChevronDown, ChevronRight, GripVertical
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Master type configuration
const MASTER_TYPES = [
  { type: 'device_type', label: 'Device Types', icon: Laptop, description: 'Laptop, Desktop, Printer, etc.' },
  { type: 'part_type', label: 'Part Types', icon: Wrench, description: 'Keyboard, Battery, RAM, etc.' },
  { type: 'service_type', label: 'Service Types', icon: Activity, description: 'Repair, Maintenance, etc.' },
  { type: 'condition', label: 'Conditions', icon: CheckCircle, description: 'New, Good, Fair, Poor' },
  { type: 'asset_status', label: 'Asset Statuses', icon: Tag, description: 'Active, In Repair, Retired' },
  { type: 'brand', label: 'Brands', icon: Tag, description: 'Dell, HP, Lenovo, etc.' },
  { type: 'duration_unit', label: 'Duration Units', icon: RefreshCw, description: 'Days, Months, Years' },
];

const MasterData = () => {
  const { token } = useAuth();
  const [masters, setMasters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState('device_type');
  const [searchQuery, setSearchQuery] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    sort_order: 0,
    is_active: true
  });

  useEffect(() => {
    fetchMasters();
  }, [selectedType, showInactive]);

  const fetchMasters = async () => {
    try {
      const response = await axios.get(`${API}/admin/masters`, {
        params: { master_type: selectedType, include_inactive: showInactive },
        headers: { Authorization: `Bearer ${token}` }
      });
      setMasters(response.data);
    } catch (error) {
      toast.error('Failed to fetch master data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name) {
      toast.error('Name is required');
      return;
    }

    try {
      const payload = {
        ...formData,
        type: selectedType,
        code: formData.code || formData.name.toUpperCase().replace(/\s+/g, '_')
      };

      if (editingItem) {
        await axios.put(`${API}/admin/masters/${editingItem.id}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Item updated');
      } else {
        await axios.post(`${API}/admin/masters`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Item created');
      }
      fetchMasters();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleToggleActive = async (item) => {
    try {
      if (item.is_active) {
        await axios.delete(`${API}/admin/masters/${item.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Item disabled');
      } else {
        await axios.put(`${API}/admin/masters/${item.id}`, { is_active: true }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Item enabled');
      }
      fetchMasters();
    } catch (error) {
      toast.error('Operation failed');
    }
  };

  const handleSeedDefaults = async () => {
    if (!window.confirm('This will add any missing default items. Continue?')) return;
    
    try {
      await axios.post(`${API}/admin/masters/seed`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Default items seeded');
      fetchMasters();
    } catch (error) {
      toast.error('Failed to seed defaults');
    }
  };

  const openCreateModal = () => {
    setEditingItem(null);
    setFormData({
      name: '',
      code: '',
      description: '',
      sort_order: masters.length + 1,
      is_active: true
    });
    setModalOpen(true);
  };

  const openEditModal = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      code: item.code || '',
      description: item.description || '',
      sort_order: item.sort_order || 0,
      is_active: item.is_active
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingItem(null);
  };

  const filteredMasters = masters.filter(m => 
    m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (m.code && m.code.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const currentTypeConfig = MASTER_TYPES.find(t => t.type === selectedType);
  const TypeIcon = currentTypeConfig?.icon || Settings2;

  return (
    <div className="space-y-6" data-testid="master-data-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Master Data</h1>
          <p className="text-slate-500 mt-1">Manage dropdown options and system values</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline"
            onClick={handleSeedDefaults}
            className="text-slate-600"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Seed Defaults
          </Button>
          <Button 
            onClick={openCreateModal}
            className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
            data-testid="add-master-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Item
          </Button>
        </div>
      </div>

      {/* Type Tabs */}
      <div className="bg-white rounded-xl border border-slate-100 p-1 flex flex-wrap gap-1">
        {MASTER_TYPES.map((type) => {
          const Icon = type.icon;
          return (
            <button
              key={type.type}
              onClick={() => {
                setSelectedType(type.type);
                setSearchQuery('');
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedType === type.type
                  ? 'bg-[#0F62FE] text-white'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
              data-testid={`tab-${type.type}`}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{type.label}</span>
            </button>
          );
        })}
      </div>

      {/* Current Type Info + Search */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="w-10 h-10 bg-[#E8F0FE] rounded-lg flex items-center justify-center">
            <TypeIcon className="h-5 w-5 text-[#0F62FE]" />
          </div>
          <div>
            <h2 className="font-medium text-slate-900">{currentTypeConfig?.label}</h2>
            <p className="text-sm text-slate-500">{currentTypeConfig?.description}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="rounded border-slate-300"
            />
            Show inactive
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input pl-9 w-48"
            />
          </div>
        </div>
      </div>

      {/* Items Table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : filteredMasters.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full table-modern">
              <thead>
                <tr>
                  <th className="w-12">#</th>
                  <th>Name</th>
                  <th>Code</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th className="w-16"></th>
                </tr>
              </thead>
              <tbody>
                {filteredMasters.map((item, index) => (
                  <tr 
                    key={item.id} 
                    className={!item.is_active ? 'opacity-50' : ''}
                    data-testid={`master-row-${item.id}`}
                  >
                    <td className="text-slate-400 text-sm">{item.sort_order || index + 1}</td>
                    <td>
                      <p className="font-medium text-slate-900">{item.name}</p>
                    </td>
                    <td>
                      <code className="text-xs bg-slate-100 px-2 py-1 rounded font-mono">
                        {item.code || '-'}
                      </code>
                    </td>
                    <td className="text-sm text-slate-500">
                      {item.description || '-'}
                    </td>
                    <td>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        item.is_active 
                          ? 'bg-emerald-50 text-emerald-600'
                          : 'bg-slate-100 text-slate-500'
                      }`}>
                        {item.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEditModal(item)}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleToggleActive(item)}
                            className={item.is_active ? 'text-amber-600' : 'text-emerald-600'}
                          >
                            {item.is_active ? (
                              <>
                                <X className="h-4 w-4 mr-2" />
                                Disable
                              </>
                            ) : (
                              <>
                                <CheckCircle className="h-4 w-4 mr-2" />
                                Enable
                              </>
                            )}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-16">
            <TypeIcon className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No {currentTypeConfig?.label.toLowerCase()} found</p>
            <Button onClick={openCreateModal} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add your first item
            </Button>
          </div>
        )}
      </div>

      {/* Count */}
      {filteredMasters.length > 0 && (
        <p className="text-sm text-slate-500">
          Showing {filteredMasters.length} of {masters.length} items
        </p>
      )}

      {/* Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingItem ? 'Edit' : 'Add'} {currentTypeConfig?.label.slice(0, -1)}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="form-input"
                placeholder="e.g., Laptop"
                data-testid="master-name-input"
              />
            </div>
            <div>
              <label className="form-label">Code</label>
              <input
                type="text"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                className="form-input font-mono"
                placeholder="Auto-generated if empty"
              />
              <p className="text-xs text-slate-500 mt-1">Used for system identification</p>
            </div>
            <div>
              <label className="form-label">Description</label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="form-input"
                placeholder="Optional description"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Sort Order</label>
                <input
                  type="number"
                  value={formData.sort_order}
                  onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) || 0 })}
                  className="form-input"
                  min="0"
                />
              </div>
              <div className="flex items-end pb-2">
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded border-slate-300"
                  />
                  Active
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button 
                type="submit" 
                className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
                data-testid="master-submit-btn"
              >
                {editingItem ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MasterData;
