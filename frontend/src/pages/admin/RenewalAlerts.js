import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AlertTriangle, Shield, FileCheck, Key, Mail, Calendar, Building2, ChevronRight, Clock, Filter } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const alertColors = {
  critical: 'bg-red-50 border-red-200 text-red-700',
  warning: 'bg-amber-50 border-amber-200 text-amber-700',
  notice: 'bg-yellow-50 border-yellow-200 text-yellow-700'
};

const alertBadgeColors = {
  critical: 'bg-red-100 text-red-700',
  warning: 'bg-amber-100 text-amber-700',
  notice: 'bg-yellow-100 text-yellow-700'
};

const RenewalAlerts = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [alerts, setAlerts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(90);
  const [activeTab, setActiveTab] = useState('all');
  const [companies, setCompanies] = useState([]);
  const [filterCompany, setFilterCompany] = useState('');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const params = { days };
      if (filterCompany) params.company_id = filterCompany;
      
      const [alertRes, compRes] = await Promise.all([
        axios.get(`${API}/admin/renewal-alerts`, { params, headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/companies`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setAlerts(alertRes.data);
      setCompanies(compRes.data);
    } catch (error) {
      toast.error('Failed to load renewal alerts');
    } finally {
      setLoading(false);
    }
  }, [token, days, filterCompany]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', { 
      day: 'numeric', month: 'short', year: 'numeric' 
    });
  };

  const tabs = [
    { id: 'all', label: 'All Alerts', count: alerts?.total_alerts || 0 },
    { id: 'warranties', label: 'Warranties', icon: Shield, count: alerts?.warranties?.length || 0 },
    { id: 'amc_contracts', label: 'AMC', icon: FileCheck, count: alerts?.amc_contracts?.length || 0 },
    { id: 'licenses', label: 'Licenses', icon: Key, count: alerts?.licenses?.length || 0 },
    { id: 'subscriptions', label: 'Subscriptions', icon: Mail, count: alerts?.subscriptions?.length || 0 },
  ];

  const getAllItems = () => {
    if (!alerts) return [];
    return [
      ...alerts.warranties.map(i => ({ ...i, category: 'warranty' })),
      ...alerts.amc_contracts.map(i => ({ ...i, category: 'amc' })),
      ...alerts.licenses.map(i => ({ ...i, category: 'license' })),
      ...alerts.subscriptions.map(i => ({ ...i, category: 'subscription' }))
    ].sort((a, b) => a.days_left - b.days_left);
  };

  const getItemsForTab = () => {
    if (!alerts) return [];
    if (activeTab === 'all') return getAllItems();
    return alerts[activeTab] || [];
  };

  const renderItem = (item) => {
    const alertClass = alertColors[item.alert_type] || alertColors.notice;
    const badgeClass = alertBadgeColors[item.alert_type] || alertBadgeColors.notice;
    
    let title, subtitle, onClick;
    
    switch (item.category || item.item_type) {
      case 'warranty':
        title = `${item.brand || ''} ${item.model || item.device_type || 'Device'}`;
        subtitle = item.serial_number;
        onClick = () => navigate(`/admin/devices/${item.id}`);
        break;
      case 'amc':
        title = item.contract_name || item.contract_number || 'AMC Contract';
        subtitle = item.vendor_name;
        onClick = () => navigate('/admin/amc-contracts');
        break;
      case 'license':
        title = item.software_name || 'License';
        subtitle = item.license_type;
        onClick = () => navigate('/admin/licenses');
        break;
      case 'subscription':
        title = item.provider_name || item.provider || 'Subscription';
        subtitle = item.domain;
        onClick = () => navigate('/admin/subscriptions');
        break;
      default:
        title = 'Item';
        subtitle = '';
        onClick = () => {};
    }

    return (
      <div 
        key={`${item.category || item.item_type}-${item.id}`}
        className={`flex items-center gap-4 p-4 rounded-lg border cursor-pointer hover:shadow-sm transition-shadow ${alertClass}`}
        onClick={onClick}
      >
        <div className="flex-shrink-0">
          {item.category === 'warranty' || item.item_type === 'warranty' ? <Shield className="h-5 w-5" /> :
           item.category === 'amc' || item.item_type === 'amc' ? <FileCheck className="h-5 w-5" /> :
           item.category === 'license' || item.item_type === 'license' ? <Key className="h-5 w-5" /> :
           <Mail className="h-5 w-5" />}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{title}</p>
          <p className="text-sm opacity-75 truncate">{subtitle}</p>
        </div>
        <div className="text-right flex-shrink-0">
          <span className={`text-xs px-2 py-1 rounded-full ${badgeClass}`}>
            {item.days_left} days
          </span>
          <p className="text-xs mt-1 opacity-75">
            {item.category === 'warranty' || item.item_type === 'warranty' ? formatDate(item.warranty_end_date) :
             item.category === 'amc' || item.item_type === 'amc' ? formatDate(item.end_date) :
             item.category === 'license' || item.item_type === 'license' ? formatDate(item.expiry_date) :
             formatDate(item.renewal_date)}
          </p>
        </div>
        <ChevronRight className="h-4 w-4 opacity-50" />
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="renewal-alerts-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Renewal Alerts</h1>
          <p className="text-slate-500">Track expiring warranties, AMC contracts, licenses, and subscriptions</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <AlertTriangle className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{alerts?.total_alerts || 0}</p>
              <p className="text-xs text-slate-500">Total Alerts</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-red-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
              <Clock className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">{alerts?.summary?.critical || 0}</p>
              <p className="text-xs text-slate-500">&lt; 30 Days</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-amber-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Clock className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-amber-600">{alerts?.summary?.warning || 0}</p>
              <p className="text-xs text-slate-500">30-60 Days</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-yellow-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-yellow-100 flex items-center justify-center">
              <Clock className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-600">{alerts?.summary?.notice || 0}</p>
              <p className="text-xs text-slate-500">60-90 Days</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-100 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <span className="text-sm text-slate-600">Filter:</span>
          </div>
          <select 
            value={days} 
            onChange={(e) => setDays(parseInt(e.target.value))} 
            className="form-select w-40"
          >
            <option value={30}>Next 30 days</option>
            <option value={60}>Next 60 days</option>
            <option value={90}>Next 90 days</option>
            <option value={180}>Next 6 months</option>
            <option value={365}>Next 1 year</option>
          </select>
          <select 
            value={filterCompany} 
            onChange={(e) => setFilterCompany(e.target.value)} 
            className="form-select w-48"
          >
            <option value="">All Companies</option>
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
      </div>

      {/* Tabs and Content */}
      <div className="bg-white rounded-xl border border-slate-100">
        {/* Tabs */}
        <div className="border-b border-slate-100 p-1 flex gap-1 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-[#0F62FE] text-white'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                {Icon && <Icon className="h-4 w-4" />}
                {tab.label}
                <span className={`px-2 py-0.5 rounded-full text-xs ${
                  activeTab === tab.id ? 'bg-white/20' : 'bg-slate-100'
                }`}>
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="p-6">
          {getItemsForTab().length > 0 ? (
            <div className="space-y-3">
              {getItemsForTab().map(item => renderItem(item))}
            </div>
          ) : (
            <div className="text-center py-12">
              <AlertTriangle className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No expiring items in this category</p>
              <p className="text-sm text-slate-400 mt-1">All items are up to date</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RenewalAlerts;
