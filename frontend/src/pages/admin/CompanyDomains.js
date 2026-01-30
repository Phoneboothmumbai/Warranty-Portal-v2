import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';
import { 
  Globe, Plus, Trash2, Check, X, AlertCircle, Building2,
  Mail, RefreshCw, Search
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function CompanyDomains() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingCompany, setEditingCompany] = useState(null);
  const [newDomain, setNewDomain] = useState('');
  const token = localStorage.getItem('admin_token');

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await axios.get(`${API}/api/admin/companies`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCompanies(response.data.companies || response.data || []);
    } catch (error) {
      toast.error('Failed to fetch companies');
    } finally {
      setLoading(false);
    }
  };

  const addDomain = async (companyId) => {
    if (!newDomain.trim()) {
      toast.error('Please enter a domain');
      return;
    }

    // Validate domain format
    const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}$/;
    if (!domainRegex.test(newDomain.trim())) {
      toast.error('Invalid domain format (e.g., example.com)');
      return;
    }

    try {
      await axios.post(`${API}/api/admin/companies/${companyId}/domains`, {
        domain: newDomain.trim().toLowerCase()
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Domain added successfully');
      setNewDomain('');
      fetchCompanies();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add domain');
    }
  };

  const removeDomain = async (companyId, domain) => {
    if (!window.confirm(`Remove domain "${domain}"?`)) return;

    try {
      await axios.delete(`${API}/api/admin/companies/${companyId}/domains/${domain}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Domain removed');
      fetchCompanies();
    } catch (error) {
      toast.error('Failed to remove domain');
    }
  };

  const filteredCompanies = companies.filter(c => 
    c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.email_domains?.some(d => d.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6" data-testid="company-domains">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Company Email Domains</h1>
          <p className="text-slate-500">Manage email domains for automatic ticket routing</p>
        </div>
        <Button variant="outline" onClick={fetchCompanies}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Info Banner */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-4 flex items-start gap-3">
          <Mail className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">How Domain Routing Works</p>
            <p>When a ticket is created via email, the system checks the sender's email domain 
            and automatically associates the ticket with the matching company. 
            For example, emails from <code className="bg-blue-100 px-1 rounded">john@acme.com</code> will 
            be routed to the company with <code className="bg-blue-100 px-1 rounded">acme.com</code> in their domains.</p>
          </div>
        </CardContent>
      </Card>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search companies or domains..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Companies List */}
      <div className="space-y-4">
        {filteredCompanies.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Building2 className="w-12 h-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No companies found</p>
            </CardContent>
          </Card>
        ) : (
          filteredCompanies.map(company => (
            <Card key={company.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Company Info */}
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-slate-100 rounded-lg">
                      <Building2 className="w-5 h-5 text-slate-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{company.name}</h3>
                      <p className="text-sm text-slate-500">{company.contact_email || 'No contact email'}</p>
                    </div>
                  </div>

                  {/* Domains */}
                  <div className="flex-1 md:px-6">
                    <div className="flex flex-wrap gap-2">
                      {company.email_domains?.length > 0 ? (
                        company.email_domains.map(domain => (
                          <div 
                            key={domain}
                            className="flex items-center gap-1 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-full"
                          >
                            <Globe className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="text-sm text-emerald-700">{domain}</span>
                            <button
                              onClick={() => removeDomain(company.id, domain)}
                              className="ml-1 p-0.5 hover:bg-emerald-100 rounded-full transition-colors"
                              title="Remove domain"
                            >
                              <X className="w-3.5 h-3.5 text-emerald-600 hover:text-red-600" />
                            </button>
                          </div>
                        ))
                      ) : (
                        <span className="text-sm text-slate-400 italic">No domains configured</span>
                      )}
                    </div>
                  </div>

                  {/* Add Domain Button */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setEditingCompany(editingCompany === company.id ? null : company.id)}
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Add Domain
                  </Button>
                </div>

                {/* Add Domain Form */}
                {editingCompany === company.id && (
                  <div className="mt-4 pt-4 border-t flex items-center gap-3">
                    <div className="flex-1 flex items-center gap-2">
                      <Globe className="w-4 h-4 text-slate-400" />
                      <input
                        type="text"
                        value={newDomain}
                        onChange={(e) => setNewDomain(e.target.value)}
                        placeholder="example.com"
                        className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        onKeyPress={(e) => e.key === 'Enter' && addDomain(company.id)}
                      />
                    </div>
                    <Button onClick={() => addDomain(company.id)} size="sm">
                      <Check className="w-4 h-4 mr-1" />
                      Add
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => {
                        setEditingCompany(null);
                        setNewDomain('');
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Summary Stats */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-500">
              {filteredCompanies.length} companies • {filteredCompanies.reduce((acc, c) => acc + (c.email_domains?.length || 0), 0)} domains configured
            </span>
            <div className="flex items-center gap-2 text-slate-400">
              <AlertCircle className="w-4 h-4" />
              <span>Domains are case-insensitive</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
