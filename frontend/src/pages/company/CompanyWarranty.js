import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { 
  Shield, Search, Filter, ChevronRight, AlertTriangle,
  Clock, CheckCircle2, XCircle, Calendar, Laptop
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyWarranty = () => {
  const { token } = useCompanyAuth();
  const [searchParams] = useSearchParams();
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState(searchParams.get('filter') || 'all');

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await axios.get(`${API}/company/devices`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDevices(response.data);
    } catch (error) {
      toast.error('Failed to load warranty data');
    } finally {
      setLoading(false);
    }
  };

  const getWarrantyStatus = (device) => {
    if (!device.warranty_end_date) return { status: 'unknown', label: 'Unknown', color: 'slate', days: null };
    
    const endDate = new Date(device.warranty_end_date);
    const today = new Date();
    const daysLeft = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));
    
    if (daysLeft < 0) return { status: 'expired', label: 'Expired', color: 'red', days: Math.abs(daysLeft) };
    if (daysLeft <= 30) return { status: 'critical', label: `${daysLeft} days`, color: 'red', days: daysLeft };
    if (daysLeft <= 60) return { status: 'warning', label: `${daysLeft} days`, color: 'amber', days: daysLeft };
    if (daysLeft <= 90) return { status: 'attention', label: `${daysLeft} days`, color: 'orange', days: daysLeft };
    return { status: 'active', label: `${daysLeft} days`, color: 'emerald', days: daysLeft };
  };

  const colorClasses = {
    red: 'bg-red-50 text-red-700 border-red-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    slate: 'bg-slate-50 text-slate-600 border-slate-200',
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  // Filter devices based on warranty status
  const filteredDevices = devices.filter(device => {
    const warranty = getWarrantyStatus(device);
    
    // Search filter
    const matchesSearch = 
      device.serial_number?.toLowerCase().includes(search.toLowerCase()) ||
      device.brand?.toLowerCase().includes(search.toLowerCase()) ||
      device.model?.toLowerCase().includes(search.toLowerCase());
    
    if (!matchesSearch) return false;

    // Status filter
    switch (filter) {
      case 'expiring':
        return warranty.days !== null && warranty.days >= 0 && warranty.days <= 30;
      case 'expiring_60':
        return warranty.days !== null && warranty.days >= 0 && warranty.days <= 60;
      case 'expiring_90':
        return warranty.days !== null && warranty.days >= 0 && warranty.days <= 90;
      case 'expired':
        return warranty.status === 'expired';
      case 'active':
        return warranty.status === 'active' || warranty.status === 'attention' || warranty.status === 'warning' || warranty.status === 'critical';
      default:
        return true;
    }
  }).sort((a, b) => {
    // Sort by warranty end date (closest to expiry first)
    const aDate = a.warranty_end_date ? new Date(a.warranty_end_date) : new Date('2099-12-31');
    const bDate = b.warranty_end_date ? new Date(b.warranty_end_date) : new Date('2099-12-31');
    return aDate - bDate;
  });

  // Summary stats
  const stats = {
    total: devices.length,
    expiring30: devices.filter(d => { const w = getWarrantyStatus(d); return w.days !== null && w.days >= 0 && w.days <= 30; }).length,
    expiring60: devices.filter(d => { const w = getWarrantyStatus(d); return w.days !== null && w.days > 30 && w.days <= 60; }).length,
    expiring90: devices.filter(d => { const w = getWarrantyStatus(d); return w.days !== null && w.days > 60 && w.days <= 90; }).length,
    expired: devices.filter(d => getWarrantyStatus(d).status === 'expired').length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-warranty-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Warranty & Coverage</h1>
        <p className="text-slate-500 mt-1">Track warranty status for all your devices</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <button 
          onClick={() => setFilter('expiring')}
          className={`p-4 rounded-xl border transition-all ${filter === 'expiring' ? 'border-red-300 bg-red-50' : 'border-slate-200 bg-white hover:border-red-200'}`}
        >
          <div className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <span className="text-2xl font-bold">{stats.expiring30}</span>
          </div>
          <p className="text-sm text-slate-500 mt-1">Expiring in 30 days</p>
        </button>
        
        <button 
          onClick={() => setFilter('expiring_60')}
          className={`p-4 rounded-xl border transition-all ${filter === 'expiring_60' ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-white hover:border-amber-200'}`}
        >
          <div className="flex items-center gap-2 text-amber-600">
            <Clock className="h-5 w-5" />
            <span className="text-2xl font-bold">{stats.expiring60}</span>
          </div>
          <p className="text-sm text-slate-500 mt-1">30-60 days left</p>
        </button>
        
        <button 
          onClick={() => setFilter('expiring_90')}
          className={`p-4 rounded-xl border transition-all ${filter === 'expiring_90' ? 'border-orange-300 bg-orange-50' : 'border-slate-200 bg-white hover:border-orange-200'}`}
        >
          <div className="flex items-center gap-2 text-orange-600">
            <Clock className="h-5 w-5" />
            <span className="text-2xl font-bold">{stats.expiring90}</span>
          </div>
          <p className="text-sm text-slate-500 mt-1">60-90 days left</p>
        </button>
        
        <button 
          onClick={() => setFilter('expired')}
          className={`p-4 rounded-xl border transition-all ${filter === 'expired' ? 'border-slate-400 bg-slate-100' : 'border-slate-200 bg-white hover:border-slate-300'}`}
        >
          <div className="flex items-center gap-2 text-slate-600">
            <XCircle className="h-5 w-5" />
            <span className="text-2xl font-bold">{stats.expired}</span>
          </div>
          <p className="text-sm text-slate-500 mt-1">Expired</p>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by serial number, brand, or model..."
              className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              data-testid="warranty-search-input"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter className="h-5 w-5 text-slate-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              data-testid="warranty-filter-select"
            >
              <option value="all">All Devices</option>
              <option value="active">Active Warranty</option>
              <option value="expiring">Expiring in 30 days</option>
              <option value="expiring_60">Expiring in 60 days</option>
              <option value="expiring_90">Expiring in 90 days</option>
              <option value="expired">Expired</option>
            </select>
          </div>
        </div>
      </div>

      {/* Device List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {filteredDevices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">Device</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">Serial Number</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">Warranty Start</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">Warranty End</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">Status</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-600"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredDevices.map((device) => {
                  const warranty = getWarrantyStatus(device);
                  return (
                    <tr 
                      key={device.id} 
                      className="hover:bg-slate-50 transition-colors"
                      data-testid={`warranty-row-${device.id}`}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                            <Laptop className="h-5 w-5 text-slate-500" />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">{device.brand} {device.model}</p>
                            <p className="text-xs text-slate-500">{device.category}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-sm text-slate-700">{device.serial_number}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{formatDate(device.warranty_start_date)}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{formatDate(device.warranty_end_date)}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${colorClasses[warranty.color]}`}>
                          {warranty.status === 'expired' ? <XCircle className="h-3 w-3" /> : 
                           warranty.status === 'active' ? <CheckCircle2 className="h-3 w-3" /> :
                           <AlertTriangle className="h-3 w-3" />}
                          {warranty.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Link 
                          to={`/company/devices/${device.id}`}
                          className="text-emerald-600 hover:text-emerald-700 text-sm font-medium"
                        >
                          View <ChevronRight className="h-4 w-4 inline" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center">
            <Shield className="h-12 w-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500">No devices found matching your criteria</p>
            <button 
              onClick={() => { setFilter('all'); setSearch(''); }}
              className="text-sm text-emerald-600 hover:text-emerald-700 mt-2"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="text-sm text-slate-500 text-center">
        Showing {filteredDevices.length} of {devices.length} devices
      </div>
    </div>
  );
};

export default CompanyWarranty;
