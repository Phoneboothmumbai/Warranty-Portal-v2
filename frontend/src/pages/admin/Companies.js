import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Plus, Search, Edit2, Trash2, Building2, X, MoreVertical, Eye } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { BulkImport } from '../../components/ui/bulk-import';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Bulk import column definitions
const bulkImportColumns = [
  { key: 'name', label: 'Company Name', required: true, example: 'Acme Corp' },
  { key: 'company_code', label: 'Company Code', required: false, example: 'ACME001' },
  { key: 'industry', label: 'Industry', required: false, example: 'Technology' },
  { key: 'contact_name', label: 'Contact Name', required: false, example: 'John Doe' },
  { key: 'contact_email', label: 'Contact Email', required: false, example: 'john@acme.com' },
  { key: 'contact_phone', label: 'Contact Phone', required: false, example: '9876543210' },
  { key: 'address', label: 'Address', required: false, example: '123 Main St' },
  { key: 'city', label: 'City', required: false, example: 'Mumbai' },
  { key: 'state', label: 'State', required: false, example: 'Maharashtra' },
  { key: 'pincode', label: 'Pincode', required: false, example: '400001' },
  { key: 'gst_number', label: 'GST Number', required: false, example: '27AAACA1234A1Z5' },
];

const sampleData = [
  { name: 'Acme Corporation', company_code: 'ACME001', industry: 'Technology', contact_name: 'John Doe', contact_email: 'john@acme.com', contact_phone: '9876543210', address: '123 Tech Park', city: 'Mumbai', state: 'Maharashtra', pincode: '400001', gst_number: '27AAACA1234A1Z5' },
  { name: 'Beta Industries', company_code: 'BETA002', industry: 'Manufacturing', contact_name: 'Jane Smith', contact_email: 'jane@beta.com', contact_phone: '9876543211', address: '456 Industrial Area', city: 'Pune', state: 'Maharashtra', pincode: '411001', gst_number: '27AAACB1234B1Z6' },
];

const Companies = () => {
  const { token } = useAuth();
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    gst_number: '',
    address: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    amc_status: 'not_applicable',
    notes: ''
  });

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await axios.get(`${API}/admin/companies`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCompanies(response.data);
    } catch (error) {
      toast.error('Failed to fetch companies');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.contact_name || !formData.contact_email || !formData.contact_phone) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      if (editingCompany) {
        await axios.put(`${API}/admin/companies/${editingCompany.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Company updated');
      } else {
        await axios.post(`${API}/admin/companies`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Company created');
      }
      fetchCompanies();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (company) => {
    if (!window.confirm(`Delete "${company.name}"? This will also delete related users.`)) return;
    
    try {
      await axios.delete(`${API}/admin/companies/${company.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Company deleted');
      fetchCompanies();
    } catch (error) {
      toast.error('Failed to delete company');
    }
  };

  const handleBulkImport = async (records) => {
    const response = await axios.post(`${API}/admin/bulk-import/companies`, 
      { records },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    fetchCompanies();
    return response.data;
  };

  const openCreateModal = () => {
    setEditingCompany(null);
    setFormData({
      name: '',
      gst_number: '',
      address: '',
      contact_name: '',
      contact_email: '',
      contact_phone: '',
      amc_status: 'not_applicable',
      notes: ''
    });
    setModalOpen(true);
  };

  const openEditModal = (company) => {
    setEditingCompany(company);
    setFormData({
      name: company.name,
      gst_number: company.gst_number || '',
      address: company.address || '',
      contact_name: company.contact_name,
      contact_email: company.contact_email,
      contact_phone: company.contact_phone,
      amc_status: company.amc_status || 'not_applicable',
      notes: company.notes || ''
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingCompany(null);
  };

  const filteredCompanies = companies.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.contact_email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const amcStatusLabel = {
    active: 'Active',
    expired: 'Expired',
    not_applicable: 'N/A'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="companies-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Companies</h1>
          <p className="text-slate-500 mt-1">Manage customer organizations</p>
        </div>
        <Button 
          onClick={openCreateModal}
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
          data-testid="add-company-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Company
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search companies..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="form-input pl-11"
          data-testid="search-companies"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {filteredCompanies.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full table-modern">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Contact</th>
                  <th>Phone</th>
                  <th>AMC Status</th>
                  <th className="w-16"></th>
                </tr>
              </thead>
              <tbody>
                {filteredCompanies.map((company) => (
                  <tr key={company.id} data-testid={`company-row-${company.id}`}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                          <Building2 className="h-4 w-4 text-slate-600" />
                        </div>
                        <div>
                          <Link 
                            to={`/admin/companies/${company.id}`} 
                            className="font-medium text-slate-900 hover:text-[#0F62FE] hover:underline"
                          >
                            {company.name}
                          </Link>
                          {company.gst_number && (
                            <p className="text-xs text-slate-500 font-mono">GST: {company.gst_number}</p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <p className="text-slate-900">{company.contact_name}</p>
                      <p className="text-xs text-slate-500">{company.contact_email}</p>
                    </td>
                    <td className="font-mono text-sm">{company.contact_phone}</td>
                    <td>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        company.amc_status === 'active' 
                          ? 'bg-emerald-50 text-emerald-600'
                          : company.amc_status === 'expired'
                          ? 'bg-red-50 text-red-600'
                          : 'bg-slate-100 text-slate-500'
                      }`}>
                        {amcStatusLabel[company.amc_status] || 'N/A'}
                      </span>
                    </td>
                    <td>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" data-testid={`company-menu-${company.id}`}>
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link to={`/admin/companies/${company.id}`}>
                              <Eye className="h-4 w-4 mr-2" />
                              View Details
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openEditModal(company)}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(company)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
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
            <Building2 className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No companies found</p>
            <Button onClick={openCreateModal} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add your first company
            </Button>
          </div>
        )}
      </div>

      {/* Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingCompany ? 'Edit Company' : 'Add Company'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Company Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="form-input"
                data-testid="company-name-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">GST Number</label>
                <input
                  type="text"
                  value={formData.gst_number}
                  onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">AMC Status</label>
                <select
                  value={formData.amc_status}
                  onChange={(e) => setFormData({ ...formData, amc_status: e.target.value })}
                  className="form-select"
                >
                  <option value="not_applicable">Not Applicable</option>
                  <option value="active">Active</option>
                  <option value="expired">Expired</option>
                </select>
              </div>
            </div>
            <div>
              <label className="form-label">Address</label>
              <textarea
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="form-input"
                rows={2}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Contact Name *</label>
                <input
                  type="text"
                  value={formData.contact_name}
                  onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                  className="form-input"
                  data-testid="company-contact-name-input"
                />
              </div>
              <div>
                <label className="form-label">Contact Phone *</label>
                <input
                  type="tel"
                  value={formData.contact_phone}
                  onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                  className="form-input"
                  data-testid="company-contact-phone-input"
                />
              </div>
            </div>
            <div>
              <label className="form-label">Contact Email *</label>
              <input
                type="email"
                value={formData.contact_email}
                onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                className="form-input"
                data-testid="company-contact-email-input"
              />
            </div>
            <div>
              <label className="form-label">Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="form-input"
                rows={2}
                placeholder="Internal notes..."
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="company-submit-btn">
                {editingCompany ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Companies;
