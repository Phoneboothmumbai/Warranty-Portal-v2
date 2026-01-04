import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Package, Search, Calendar, MapPin, ChevronDown, ChevronUp,
  Laptop, Tag, Building2
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyDeployments = () => {
  const { token } = useCompanyAuth();
  const [deployments, setDeployments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedDeployment, setExpandedDeployment] = useState(null);

  useEffect(() => {
    fetchDeployments();
  }, []);

  const fetchDeployments = async () => {
    try {
      const response = await axios.get(`${API}/company/deployments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDeployments(response.data);
    } catch (error) {
      toast.error('Failed to load deployments');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const filteredDeployments = deployments.filter(deployment =>
    deployment.deployment_number?.toLowerCase().includes(search.toLowerCase()) ||
    deployment.site_name?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-deployments-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Deployments</h1>
        <p className="text-slate-500 mt-1">View your asset deployments and installation records</p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search deployments..."
            className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            data-testid="deployment-search-input"
          />
        </div>
      </div>

      {/* Deployment List */}
      <div className="space-y-4">
        {filteredDeployments.length > 0 ? (
          filteredDeployments.map((deployment) => {
            const isExpanded = expandedDeployment === deployment.id;
            
            return (
              <div 
                key={deployment.id} 
                className="bg-white rounded-xl border border-slate-200 overflow-hidden"
                data-testid={`deployment-${deployment.id}`}
              >
                <button
                  onClick={() => setExpandedDeployment(isExpanded ? null : deployment.id)}
                  className="w-full p-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center">
                      <Package className="h-6 w-6 text-blue-600" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-slate-900">
                        {deployment.deployment_number || `Deployment #${deployment.id.slice(-6)}`}
                      </h3>
                      <div className="flex items-center gap-3 text-sm text-slate-500 mt-0.5">
                        {deployment.site_name && (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3.5 w-3.5" />
                            {deployment.site_name}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          {formatDate(deployment.deployment_date)}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 rounded-full text-sm font-medium text-slate-700">
                      <Laptop className="h-4 w-4" />
                      {deployment.items?.length || 0} items
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
                    {/* Deployment Info */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
                      <div className="bg-slate-50 rounded-lg p-4">
                        <p className="text-xs text-slate-500 uppercase tracking-wide">Deployment Date</p>
                        <p className="font-medium text-slate-900 mt-1">{formatDate(deployment.deployment_date)}</p>
                      </div>
                      
                      <div className="bg-slate-50 rounded-lg p-4">
                        <p className="text-xs text-slate-500 uppercase tracking-wide">Site</p>
                        <p className="font-medium text-slate-900 mt-1">{deployment.site_name || 'N/A'}</p>
                      </div>
                      
                      <div className="bg-slate-50 rounded-lg p-4">
                        <p className="text-xs text-slate-500 uppercase tracking-wide">Total Items</p>
                        <p className="font-medium text-slate-900 mt-1">{deployment.items?.length || 0}</p>
                      </div>
                    </div>

                    {/* Items List */}
                    {deployment.items && deployment.items.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-semibold text-slate-900 mb-3">Deployed Items</h4>
                        <div className="bg-slate-50 rounded-lg overflow-hidden">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-slate-200">
                                <th className="text-left px-4 py-2 text-slate-500 font-medium">Category</th>
                                <th className="text-left px-4 py-2 text-slate-500 font-medium">Brand / Model</th>
                                <th className="text-left px-4 py-2 text-slate-500 font-medium">Serial Number</th>
                                <th className="text-left px-4 py-2 text-slate-500 font-medium">Qty</th>
                              </tr>
                            </thead>
                            <tbody>
                              {deployment.items.map((item, index) => (
                                <tr key={index} className="border-b border-slate-100 last:border-0">
                                  <td className="px-4 py-2 text-slate-900">{item.category}</td>
                                  <td className="px-4 py-2 text-slate-900">{item.brand} {item.model}</td>
                                  <td className="px-4 py-2 font-mono text-slate-600">{item.serial_number || '-'}</td>
                                  <td className="px-4 py-2 text-slate-900">{item.quantity || 1}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Notes */}
                    {deployment.notes && (
                      <div className="mt-4">
                        <h4 className="text-sm font-semibold text-slate-900 mb-2">Notes</h4>
                        <p className="text-sm text-slate-600 bg-slate-50 rounded-lg p-3">{deployment.notes}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Package className="h-12 w-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500">No deployments found</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompanyDeployments;
