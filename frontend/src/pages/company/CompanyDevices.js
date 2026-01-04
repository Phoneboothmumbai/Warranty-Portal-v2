import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { 
  Laptop, Search, Filter, ChevronRight, Shield, AlertTriangle,
  Clock, CheckCircle2, XCircle, Calendar
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyDevices = () => {
  const { token } = useCompanyAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [warrantyFilter, setWarrantyFilter] = useState(searchParams.get('warranty') || 'all');

  useEffect(() => {
    fetchDevices();
  }, [warrantyFilter]);

  const fetchDevices = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (warrantyFilter !== 'all') params.append('warranty_status', warrantyFilter);
      
      const response = await axios.get(`${API}/company/devices?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDevices(response.data);
    } catch (error) {
      toast.error('Failed to load devices');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchDevices();
  };

  const getWarrantyStatus = (device) => {
    if (!device.warranty_end_date) return { status: 'unknown', label: 'Unknown', color: 'slate' };
    
    const endDate = new Date(device.warranty_end_date);
    const today = new Date();
    const daysLeft = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));
    
    if (daysLeft < 0) return { status: 'expired', label: 'Expired', color: 'red', days: Math.abs(daysLeft) };
    if (daysLeft <= 30) return { status: 'critical', label: `${daysLeft} days left`, color: 'red', days: daysLeft };
    if (daysLeft <= 60) return { status: 'warning', label: `${daysLeft} days left`, color: 'amber', days: daysLeft };
    if (daysLeft <= 90) return { status: 'attention', label: `${daysLeft} days left`, color: 'orange', days: daysLeft };
    return { status: 'active', label: 'Active', color: 'emerald', days: daysLeft };
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'expired': return <XCircle className="h-4 w-4" />;
      case 'critical': return <AlertTriangle className="h-4 w-4" />;
      case 'warning': return <Clock className="h-4 w-4" />;
      case 'attention': return <Clock className="h-4 w-4" />;
      default: return <CheckCircle2 className="h-4 w-4" />;
    }
  };

  const colorClasses = {
    red: 'bg-red-50 text-red-700 border-red-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    slate: 'bg-slate-50 text-slate-600 border-slate-200',
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-devices-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Devices</h1>
          <p className="text-slate-500 mt-1">View all your registered devices and their warranty status</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by serial number, model, or category..."
                className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                data-testid="device-search-input"
              />
            </div>
          </form>
          
          <div className="flex items-center gap-2">
            <Filter className="h-5 w-5 text-slate-400" />
            <select
              value={warrantyFilter}
              onChange={(e) => setWarrantyFilter(e.target.value)}
              className="px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              data-testid="warranty-filter-select"
            >
              <option value="all">All Devices</option>
              <option value="active">Active Warranty</option>
              <option value="expiring_30">Expiring in 30 days</option>
              <option value="expiring_60">Expiring in 60 days</option>
              <option value="expiring_90">Expiring in 90 days</option>
              <option value="expired">Expired</option>
            </select>
          </div>
        </div>
      </div>

      {/* Device List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {devices.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {devices.map((device) => {
              const warranty = getWarrantyStatus(device);
              return (
                <Link
                  key={device.id}
                  to={`/company/devices/${device.id}`}
                  className="flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
                  data-testid={`device-row-${device.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center">
                      <Laptop className="h-6 w-6 text-slate-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-900">{device.serial_number}</h3>
                      <p className="text-sm text-slate-500">
                        {device.category} • {device.brand} {device.model}
                      </p>
                      {device.site_name && (
                        <p className="text-xs text-slate-400 mt-0.5">Site: {device.site_name}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border ${colorClasses[warranty.color]}`}>
                      {getStatusIcon(warranty.status)}
                      {warranty.label}
                    </div>
                    <ChevronRight className="h-5 w-5 text-slate-400" />
                  </div>
                </Link>
              );
            })}
          </div>
        ) : (
          <div className="p-12 text-center">
            <Laptop className="h-12 w-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500">No devices found</p>
            <p className="text-sm text-slate-400 mt-1">Try adjusting your search or filters</p>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="text-sm text-slate-500 text-center">
        Showing {devices.length} device{devices.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
};

export default CompanyDevices;
