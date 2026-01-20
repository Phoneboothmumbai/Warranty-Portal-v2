import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, Search, Edit2, Trash2, MoreVertical, Building2, Layers, Monitor, Camera, Server, Wifi, Users, Laptop, Eye, Package } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';
import { SmartSelect } from '../../components/ui/smart-select';
import { QuickCreateCompany } from '../../components/forms';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const groupTypeIcons = {
  WORKSTATION: Monitor,
  CCTV_SYSTEM: Camera,
  SERVER_RACK: Server,
  NETWORK_SETUP: Wifi,
  CONFERENCE_ROOM: Users,
  CUSTOM: Layers,
};

const groupTypeColors = {
  WORKSTATION: 'bg-blue-100 text-blue-700',
  CCTV_SYSTEM: 'bg-purple-100 text-purple-700',
  SERVER_RACK: 'bg-slate-100 text-slate-700',
  NETWORK_SETUP: 'bg-emerald-100 text-emerald-700',
  CONFERENCE_ROOM: 'bg-amber-100 text-amber-700',
  CUSTOM: 'bg-pink-100 text-pink-700',
};

const AssetGroups = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [groups, setGroups] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [devices, setDevices] = useState([]);
  const [accessories, setAccessories] = useState([]);
  const [groupTypes, setGroupTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  const [filterType, setFilterType] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [editingGroup, setEditingGroup] = useState(null);
  
  const [formData, setFormData] = useState({
    company_id: '',
    name: '',
    description: '',
    group_type: 'WORKSTATION',
    primary_device_id: '',
    device_ids: [],
    accessory_ids: [],
    location: '',
    notes: ''
  });

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [groupRes, compRes, typeRes] = await Promise.all([
        axios.get(`${API}/admin/asset-groups`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/companies`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/masters`, { params: { master_type: 'asset_group_type' }, headers: { Authorization: `Bearer ${token}` } })
      ]);
      setGroups(groupRes.data);
      setCompanies(compRes.data);
      setGroupTypes(typeRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Fetch devices and accessories when company changes
  useEffect(() => {
    const fetchCompanyAssets = async () => {
      if (formData.company_id) {
        try {
          const [devRes, accRes] = await Promise.all([
            axios.get(`${API}/admin/devices`, { params: { company_id: formData.company_id }, headers: { Authorization: `Bearer ${token}` } }),
            axios.get(`${API}/admin/accessories`, { params: { company_id: formData.company_id }, headers: { Authorization: `Bearer ${token}` } })
          ]);
          setDevices(devRes.data);
          setAccessories(accRes.data);
        } catch (e) {
          setDevices([]);
          setAccessories([]);
        }
      } else {
        setDevices([]);
        setAccessories([]);
      }
    };
    fetchCompanyAssets();
  }, [formData.company_id, token]);

  const filtered = groups.filter(g => {
    const matchesSearch = !searchQuery || 
      g.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCompany = !filterCompany || g.company_id === filterCompany;
    const matchesType = !filterType || g.group_type === filterType;
    return matchesSearch && matchesCompany && matchesType;
  });

  const stats = {
    total: groups.length,
    workstations: groups.filter(g => g.group_type === 'WORKSTATION').length,
    cctv: groups.filter(g => g.group_type === 'CCTV_SYSTEM').length,
    other: groups.filter(g => !['WORKSTATION', 'CCTV_SYSTEM'].includes(g.group_type)).length
  };

  const openCreateModal = () => {
    setEditingGroup(null);
    setFormData({
      company_id: filterCompany || '',
      name: '',
      description: '',
      group_type: 'WORKSTATION',
      primary_device_id: '',
      device_ids: [],
      accessory_ids: [],
      location: '',
      notes: ''
    });
    setModalOpen(true);
  };

  const openEditModal = (group) => {
    setEditingGroup(group);
    setFormData({
      company_id: group.company_id || '',
      name: group.name || '',
      description: group.description || '',
      group_type: group.group_type || 'CUSTOM',
      primary_device_id: group.primary_device_id || '',
      device_ids: group.device_ids || [],
      accessory_ids: group.accessory_ids || [],
      location: group.location || '',
      notes: group.notes || ''
    });
    setModalOpen(true);
  };

  const openDetailModal = async (group) => {
    try {
      const res = await axios.get(`${API}/admin/asset-groups/${group.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedGroup(res.data);
      setDetailModalOpen(true);
    } catch (error) {
      toast.error('Failed to load group details');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_id || !formData.name) {
      toast.error('Please fill required fields');
      return;
    }

    try {
      if (editingGroup) {
        await axios.put(`${API}/admin/asset-groups/${editingGroup.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Asset group updated');
      } else {
        await axios.post(`${API}/admin/asset-groups`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Asset group created');
      }
      setModalOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save');
    }
  };

  const handleDelete = async (group) => {
    if (!window.confirm(`Delete "${group.name}"?`)) return;
    try {
      await axios.delete(`${API}/admin/asset-groups/${group.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Asset group deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const toggleDevice = (deviceId) => {
    const current = formData.device_ids || [];
    if (current.includes(deviceId)) {
      setFormData({ ...formData, device_ids: current.filter(id => id !== deviceId) });
    } else {
      setFormData({ ...formData, device_ids: [...current, deviceId] });
    }
  };

  const toggleAccessory = (accId) => {
    const current = formData.accessory_ids || [];
    if (current.includes(accId)) {
      setFormData({ ...formData, accessory_ids: current.filter(id => id !== accId) });
    } else {
      setFormData({ ...formData, accessory_ids: [...current, accId] });
    }
  };

  return (
    <div className="space-y-6" data-testid="asset-groups-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Asset Groups</h1>
          <p className="text-slate-500">Bundle related devices together (Workstations, CCTV Systems, etc.)</p>
        </div>
        <Button onClick={openCreateModal} className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="add-group-btn">
          <Plus className="h-4 w-4 mr-2" />
          Create Group
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <Layers className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              <p className="text-xs text-slate-500">Total Groups</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Monitor className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.workstations}</p>
              <p className="text-xs text-slate-500">Workstations</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Camera className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.cctv}</p>
              <p className="text-xs text-slate-500">CCTV Systems</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Layers className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.other}</p>
              <p className="text-xs text-slate-500">Other</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-100 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search groups..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input pl-10"
            />
          </div>
          <select value={filterCompany} onChange={(e) => setFilterCompany(e.target.value)} className="form-select w-48">
            <option value="">All Companies</option>
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="form-select w-40">
            <option value="">All Types</option>
            {groupTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
          </select>
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((group) => {
            const Icon = groupTypeIcons[group.group_type] || Layers;
            const colorClass = groupTypeColors[group.group_type] || 'bg-slate-100 text-slate-700';
            return (
              <div 
                key={group.id} 
                className="bg-white rounded-xl border border-slate-100 p-5 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => openDetailModal(group)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClass}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <button className="p-1.5 hover:bg-slate-100 rounded-lg">
                        <MoreVertical className="h-4 w-4 text-slate-400" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openDetailModal(group); }}>
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openEditModal(group); }}>
                        <Edit2 className="h-4 w-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-red-600" onClick={(e) => { e.stopPropagation(); handleDelete(group); }}>
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <h3 className="font-semibold text-slate-900 mb-1">{group.name}</h3>
                <p className="text-sm text-slate-500 mb-3">{group.company_name}</p>
                {group.description && (
                  <p className="text-xs text-slate-400 mb-3 line-clamp-2">{group.description}</p>
                )}
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Laptop className="h-3.5 w-3.5" />
                    {group.device_count} devices
                  </span>
                  <span className="flex items-center gap-1">
                    <Package className="h-3.5 w-3.5" />
                    {group.accessory_count} accessories
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-100 p-12 text-center">
          <Layers className="h-12 w-12 mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500">No asset groups found</p>
          <Button onClick={openCreateModal} className="mt-4" variant="outline">
            Create Your First Group
          </Button>
        </div>
      )}

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingGroup ? 'Edit Asset Group' : 'Create Asset Group'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Company *</label>
                <SmartSelect
                  value={formData.company_id}
                  onChange={(val) => setFormData({ ...formData, company_id: val, device_ids: [], accessory_ids: [], primary_device_id: '' })}
                  options={companies.map(c => ({ value: c.id, label: c.name }))}
                  placeholder="Select company"
                  quickCreate={<QuickCreateCompany onCreated={(c) => { setCompanies([...companies, c]); setFormData({ ...formData, company_id: c.id }); }} />}
                />
              </div>
              <div>
                <label className="form-label">Group Type *</label>
                <select
                  value={formData.group_type}
                  onChange={(e) => setFormData({ ...formData, group_type: e.target.value })}
                  className="form-select"
                >
                  {groupTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
                </select>
              </div>
              <div className="col-span-2">
                <label className="form-label">Group Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="form-input"
                  placeholder="e.g., Workstation - John's Desk, CCTV System - Floor 1"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="form-input"
                  rows={2}
                  placeholder="Brief description of this asset group"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Location</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="form-input"
                  placeholder="e.g., 2nd Floor, Room 201"
                />
              </div>
            </div>

            {/* Device Selection */}
            {formData.company_id && (
              <>
                <div>
                  <label className="form-label">Select Devices ({formData.device_ids.length} selected)</label>
                  <div className="border rounded-lg max-h-48 overflow-y-auto">
                    {devices.length > 0 ? devices.map(d => (
                      <label 
                        key={d.id} 
                        className="flex items-center gap-3 p-3 hover:bg-slate-50 cursor-pointer border-b last:border-b-0"
                      >
                        <input
                          type="checkbox"
                          checked={formData.device_ids.includes(d.id)}
                          onChange={() => toggleDevice(d.id)}
                          className="w-4 h-4 rounded border-slate-300 text-[#0F62FE]"
                        />
                        <Laptop className="h-4 w-4 text-slate-400" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{d.brand} {d.model || d.device_type}</p>
                          <p className="text-xs text-slate-500">{d.serial_number}</p>
                        </div>
                        <span className="text-xs text-slate-400">{d.device_type}</span>
                      </label>
                    )) : (
                      <p className="text-center py-4 text-slate-400 text-sm">No devices for this company</p>
                    )}
                  </div>
                </div>

                {/* Accessory Selection */}
                <div>
                  <label className="form-label">Select Accessories ({formData.accessory_ids.length} selected)</label>
                  <div className="border rounded-lg max-h-48 overflow-y-auto">
                    {accessories.length > 0 ? accessories.map(a => (
                      <label 
                        key={a.id} 
                        className="flex items-center gap-3 p-3 hover:bg-slate-50 cursor-pointer border-b last:border-b-0"
                      >
                        <input
                          type="checkbox"
                          checked={formData.accessory_ids.includes(a.id)}
                          onChange={() => toggleAccessory(a.id)}
                          className="w-4 h-4 rounded border-slate-300 text-[#0F62FE]"
                        />
                        <Package className="h-4 w-4 text-slate-400" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{a.name}</p>
                          <p className="text-xs text-slate-500">{a.brand} {a.model}</p>
                        </div>
                        <span className="text-xs text-slate-400">{a.accessory_type}</span>
                      </label>
                    )) : (
                      <p className="text-center py-4 text-slate-400 text-sm">No accessories for this company</p>
                    )}
                  </div>
                </div>

                {/* Primary Device */}
                {formData.device_ids.length > 0 && (
                  <div>
                    <label className="form-label">Primary Device (main device in group)</label>
                    <select
                      value={formData.primary_device_id}
                      onChange={(e) => setFormData({ ...formData, primary_device_id: e.target.value })}
                      className="form-select"
                    >
                      <option value="">Select primary device</option>
                      {devices.filter(d => formData.device_ids.includes(d.id)).map(d => (
                        <option key={d.id} value={d.id}>{d.brand} {d.model} - {d.serial_number}</option>
                      ))}
                    </select>
                  </div>
                )}
              </>
            )}

            <div>
              <label className="form-label">Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="form-input"
                rows={2}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                {editingGroup ? 'Update Group' : 'Create Group'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Asset Group Details</DialogTitle>
          </DialogHeader>
          {selectedGroup && (
            <div className="space-y-6 mt-4">
              <div className="flex items-start gap-4">
                <div className={`w-16 h-16 rounded-xl flex items-center justify-center ${groupTypeColors[selectedGroup.group_type]}`}>
                  {(() => { const Icon = groupTypeIcons[selectedGroup.group_type] || Layers; return <Icon className="h-8 w-8" />; })()}
                </div>
                <div>
                  <h3 className="text-xl font-bold">{selectedGroup.name}</h3>
                  <p className="text-slate-500">{selectedGroup.company_name}</p>
                  {selectedGroup.description && <p className="text-sm text-slate-400 mt-1">{selectedGroup.description}</p>}
                </div>
              </div>

              {/* Devices */}
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Laptop className="h-4 w-4" />
                  Devices ({selectedGroup.devices?.length || 0})
                </h4>
                {selectedGroup.devices?.length > 0 ? (
                  <div className="space-y-2">
                    {selectedGroup.devices.map(d => (
                      <div 
                        key={d.id} 
                        className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer hover:bg-slate-100 ${
                          d.id === selectedGroup.primary_device_id ? 'bg-blue-50 border border-blue-200' : 'bg-slate-50'
                        }`}
                        onClick={() => navigate(`/admin/devices/${d.id}`)}
                      >
                        <Laptop className="h-5 w-5 text-slate-400" />
                        <div className="flex-1">
                          <p className="font-medium">{d.brand} {d.model || d.device_type}</p>
                          <p className="text-xs text-slate-500">{d.serial_number}</p>
                        </div>
                        {d.id === selectedGroup.primary_device_id && (
                          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Primary</span>
                        )}
                        <span className="text-xs text-slate-400">{d.device_type}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No devices in this group</p>
                )}
              </div>

              {/* Accessories */}
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Accessories ({selectedGroup.accessories?.length || 0})
                </h4>
                {selectedGroup.accessories?.length > 0 ? (
                  <div className="space-y-2">
                    {selectedGroup.accessories.map(a => (
                      <div key={a.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                        <Package className="h-5 w-5 text-slate-400" />
                        <div className="flex-1">
                          <p className="font-medium">{a.name}</p>
                          <p className="text-xs text-slate-500">{a.brand} {a.model}</p>
                        </div>
                        <span className="text-xs text-slate-400">{a.accessory_type}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No accessories in this group</p>
                )}
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => { setDetailModalOpen(false); openEditModal(selectedGroup); }}>
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit Group
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AssetGroups;
