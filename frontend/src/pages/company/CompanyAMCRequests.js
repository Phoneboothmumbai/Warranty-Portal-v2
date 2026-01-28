import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  FileText, Plus, Clock, CheckCircle2, XCircle, AlertTriangle,
  Calendar, Package, ChevronRight, Filter, Search, RefreshCw
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusConfig = {
  pending_review: { label: 'Pending Review', color: 'bg-amber-100 text-amber-700', icon: Clock },
  under_review: { label: 'Under Review', color: 'bg-blue-100 text-blue-700', icon: RefreshCw },
  approved: { label: 'Approved', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2 },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: XCircle },
  changes_requested: { label: 'Changes Requested', color: 'bg-orange-100 text-orange-700', icon: AlertTriangle },
  cancelled: { label: 'Cancelled', color: 'bg-slate-100 text-slate-600', icon: XCircle }
};

const amcTypeLabels = {
  comprehensive: 'Comprehensive',
  non_comprehensive: 'Non-Comprehensive',
  on_call: 'On-Call Basis'
};

const CompanyAMCRequests = () => {
  const { token } = useCompanyAuth();
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchRequests = useCallback(async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/company/amc-requests`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRequests(res.data);
    } catch (error) {
      toast.error('Failed to load AMC requests');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const filteredRequests = requests.filter(req => {
    if (statusFilter && req.status !== statusFilter) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        req.amc_type?.toLowerCase().includes(query) ||
        req.package_name?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    if (!amount) return '-';
    return `₹${amount.toLocaleString('en-IN')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-amc-requests">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">AMC Requests</h1>
          <p className="text-slate-500">Request and manage your Annual Maintenance Contracts</p>
        </div>
        <Button onClick={() => navigate('/company/amc-requests/new')} data-testid="new-amc-request-btn">
          <Plus className="h-4 w-4 mr-2" />
          Request AMC
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Total Requests</p>
          <p className="text-2xl font-semibold text-slate-900">{requests.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Pending</p>
          <p className="text-2xl font-semibold text-amber-600">
            {requests.filter(r => ['pending_review', 'under_review'].includes(r.status)).length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Approved</p>
          <p className="text-2xl font-semibold text-emerald-600">
            {requests.filter(r => r.status === 'approved').length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Action Required</p>
          <p className="text-2xl font-semibold text-orange-600">
            {requests.filter(r => r.status === 'changes_requested').length}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search requests..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
        >
          <option value="">All Status</option>
          {Object.entries(statusConfig).map(([key, config]) => (
            <option key={key} value={key}>{config.label}</option>
          ))}
        </select>
      </div>

      {/* Requests List */}
      {filteredRequests.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-100 p-12 text-center">
          <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">No AMC Requests</h3>
          <p className="text-slate-500 mb-4">You haven&apos;t submitted any AMC requests yet.</p>
          <Button onClick={() => navigate('/company/amc-requests/new')}>
            <Plus className="h-4 w-4 mr-2" />
            Request AMC
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredRequests.map((request) => {
            const status = statusConfig[request.status] || statusConfig.pending_review;
            const StatusIcon = status.icon;
            
            return (
              <div 
                key={request.id}
                onClick={() => navigate(`/company/amc-requests/${request.id}`)}
                className="bg-white rounded-xl border border-slate-100 p-5 hover:border-blue-200 hover:shadow-sm transition-all cursor-pointer"
                data-testid={`amc-request-${request.id}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
                      <FileText className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-slate-900">
                          {amcTypeLabels[request.amc_type] || request.amc_type} AMC
                        </h3>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${status.color}`}>
                          <StatusIcon className="h-3 w-3" />
                          {status.label}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500">
                        <span className="flex items-center gap-1">
                          <Package className="h-3.5 w-3.5" />
                          {request.device_count} devices
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          {request.duration_months} months
                        </span>
                        <span>Starts: {formatDate(request.preferred_start_date)}</span>
                      </div>
                      {request.total_price && (
                        <p className="text-sm font-medium text-emerald-600 mt-1">
                          Quoted: {formatCurrency(request.total_price)}
                        </p>
                      )}
                      {request.status === 'changes_requested' && request.changes_requested_note && (
                        <p className="text-sm text-orange-600 mt-2 bg-orange-50 p-2 rounded">
                          <AlertTriangle className="h-3.5 w-3.5 inline mr-1" />
                          {request.changes_requested_note}
                        </p>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-slate-400 flex-shrink-0" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default CompanyAMCRequests;
