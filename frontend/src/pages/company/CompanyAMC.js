import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  FileText, Search, Calendar, CheckCircle2, Clock, AlertTriangle,
  XCircle, ChevronDown, ChevronUp, Building2
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyAMC = () => {
  const { token } = useCompanyAuth();
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedContract, setExpandedContract] = useState(null);

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      const response = await axios.get(`${API}/company/amc-contracts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setContracts(response.data);
    } catch (error) {
      toast.error('Failed to load AMC contracts');
    } finally {
      setLoading(false);
    }
  };

  const getContractStatus = (contract) => {
    if (!contract.end_date) return { status: 'unknown', label: 'Unknown', color: 'slate' };
    
    const endDate = new Date(contract.end_date);
    const today = new Date();
    const daysLeft = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));
    
    if (daysLeft < 0) return { status: 'expired', label: 'Expired', color: 'red', icon: XCircle };
    if (daysLeft <= 30) return { status: 'expiring', label: `Expiring in ${daysLeft} days`, color: 'amber', icon: AlertTriangle };
    if (daysLeft <= 60) return { status: 'attention', label: `${daysLeft} days remaining`, color: 'orange', icon: Clock };
    return { status: 'active', label: 'Active', color: 'emerald', icon: CheckCircle2 };
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const colorClasses = {
    red: 'bg-red-50 text-red-700 border-red-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    slate: 'bg-slate-50 text-slate-600 border-slate-200',
  };

  const filteredContracts = contracts.filter(contract =>
    contract.contract_number?.toLowerCase().includes(search.toLowerCase()) ||
    contract.type?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-amc-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">AMC Contracts</h1>
        <p className="text-slate-500 mt-1">View your annual maintenance contracts and coverage</p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search contracts..."
            className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            data-testid="amc-search-input"
          />
        </div>
      </div>

      {/* Contract List */}
      <div className="space-y-4">
        {filteredContracts.length > 0 ? (
          filteredContracts.map((contract) => {
            const status = getContractStatus(contract);
            const StatusIcon = status.icon;
            const isExpanded = expandedContract === contract.id;
            
            return (
              <div 
                key={contract.id} 
                className="bg-white rounded-xl border border-slate-200 overflow-hidden"
                data-testid={`amc-contract-${contract.id}`}
              >
                <button
                  onClick={() => setExpandedContract(isExpanded ? null : contract.id)}
                  className="w-full p-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClasses[status.color]}`}>
                      <FileText className="h-6 w-6" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-slate-900">{contract.contract_number || 'AMC Contract'}</h3>
                      <p className="text-sm text-slate-500">{contract.type || 'Standard'} • {contract.covered_devices_count || 0} devices covered</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border ${colorClasses[status.color]}`}>
                      <StatusIcon className="h-4 w-4" />
                      {status.label}
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="h-5 w-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-slate-400" />
                    )}
                  </div>
                </button>

                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-slate-100">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4">
                      <div className="bg-slate-50 rounded-lg p-4">
                        <p className="text-xs text-slate-500 uppercase tracking-wide">Contract Period</p>
                        <p className="font-medium text-slate-900 mt-1">
                          {formatDate(contract.start_date)} - {formatDate(contract.end_date)}
                        </p>
                      </div>
                      
                      <div className="bg-slate-50 rounded-lg p-4">
                        <p className="text-xs text-slate-500 uppercase tracking-wide">Contract Type</p>
                        <p className="font-medium text-slate-900 mt-1">{contract.type || 'Standard'}</p>
                      </div>
                      
                      <div className="bg-slate-50 rounded-lg p-4">
                        <p className="text-xs text-slate-500 uppercase tracking-wide">Covered Devices</p>
                        <p className="font-medium text-slate-900 mt-1">{contract.covered_devices_count || 0}</p>
                      </div>
                    </div>

                    {/* Coverage Details */}
                    {contract.coverage_details && (
                      <div className="mt-4">
                        <h4 className="text-sm font-semibold text-slate-900 mb-2">Coverage Includes</h4>
                        <ul className="space-y-1">
                          {contract.coverage_details.map((item, index) => (
                            <li key={index} className="flex items-center gap-2 text-sm text-slate-600">
                              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Service Visits */}
                    {contract.service_visits !== undefined && (
                      <div className="mt-4 flex items-center gap-4">
                        <div className="bg-emerald-50 rounded-lg px-4 py-2">
                          <p className="text-xs text-emerald-600">Service Visits Used</p>
                          <p className="font-semibold text-emerald-700">
                            {contract.service_visits_used || 0} / {contract.service_visits || 'Unlimited'}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <FileText className="h-12 w-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500">No AMC contracts found</p>
            <p className="text-sm text-slate-400 mt-1">Contact your administrator for contract information</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompanyAMC;
