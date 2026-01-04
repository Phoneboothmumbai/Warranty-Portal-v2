import { useState, useEffect } from 'react';
import axios from 'axios';
import { MapPin, Search, Building2, Phone, Mail, Laptop } from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanySites = () => {
  const { token } = useCompanyAuth();
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchSites();
  }, []);

  const fetchSites = async () => {
    try {
      const response = await axios.get(`${API}/company/sites`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSites(response.data);
    } catch (error) {
      toast.error('Failed to load sites');
    } finally {
      setLoading(false);
    }
  };

  const filteredSites = sites.filter(site =>
    site.name?.toLowerCase().includes(search.toLowerCase()) ||
    site.city?.toLowerCase().includes(search.toLowerCase()) ||
    site.address?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-sites-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Sites</h1>
        <p className="text-slate-500 mt-1">View your company locations and branches</p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search sites by name, city, or address..."
            className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            data-testid="site-search-input"
          />
        </div>
      </div>

      {/* Site List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredSites.length > 0 ? (
          filteredSites.map((site) => (
            <div 
              key={site.id} 
              className="bg-white rounded-xl border border-slate-200 p-5 hover:border-emerald-200 transition-colors"
              data-testid={`site-card-${site.id}`}
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <MapPin className="h-6 w-6 text-blue-600" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-slate-900">{site.name}</h3>
                  
                  {site.address && (
                    <p className="text-sm text-slate-500 mt-1">{site.address}</p>
                  )}
                  
                  {(site.city || site.state || site.pincode) && (
                    <p className="text-sm text-slate-500">
                      {[site.city, site.state, site.pincode].filter(Boolean).join(', ')}
                    </p>
                  )}

                  <div className="flex flex-wrap items-center gap-3 mt-3">
                    {site.device_count !== undefined && (
                      <span className="flex items-center gap-1.5 text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full">
                        <Laptop className="h-3.5 w-3.5" />
                        {site.device_count} devices
                      </span>
                    )}
                    {site.contact_phone && (
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        <Phone className="h-3 w-3" />
                        {site.contact_phone}
                      </span>
                    )}
                    {site.contact_email && (
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        <Mail className="h-3 w-3" />
                        {site.contact_email}
                      </span>
                    )}
                  </div>

                  {site.contact_person && (
                    <p className="text-xs text-slate-400 mt-2">
                      Contact: {site.contact_person}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full bg-white rounded-xl border border-slate-200 p-12 text-center">
            <MapPin className="h-12 w-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500">No sites found</p>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="text-sm text-slate-500 text-center">
        {filteredSites.length} site{filteredSites.length !== 1 ? 's' : ''} found
      </div>
    </div>
  );
};

export default CompanySites;
