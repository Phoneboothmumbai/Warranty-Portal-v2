import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, Search, Edit2, Trash2, Users, MoreVertical, Building2, Upload, Download, User, Eye } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';
import { SmartSelect } from '../../components/ui/smart-select';
import { QuickCreateCompany } from '../../components/forms';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Employees = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [bulkUploadOpen, setBulkUploadOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadResults, setUploadResults] = useState(null);
  const [uploading, setUploading] = useState(false);
  
  const [formData, setFormData] = useState({
    company_id: '',
    employee_id: '',
    name: '',
    email: '',
    phone: '',
    department: '',
    designation: '',
    location: ''
  });

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const params = { limit: 200 };
      if (filterCompany) params.company_id = filterCompany;
      if (searchQuery) params.q = searchQuery;
      
      const [empRes, compRes] = await Promise.all([
        axios.get(`${API}/admin/company-employees`, { params, headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/companies`, { params: { limit: 500 }, headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setEmployees(empRes.data);
      setCompanies(compRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [token, filterCompany, searchQuery]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getCompanyName = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company ? company.name : 'Unknown';
  };

  const openCreateModal = () => {
    setEditingEmployee(null);
    setFormData({
      company_id: filterCompany || '',
      employee_id: '',
      name: '',
      email: '',
      phone: '',
      department: '',
      designation: '',
      location: ''
    });
    setModalOpen(true);
  };

  const openEditModal = (employee) => {
    setEditingEmployee(employee);
    setFormData({
      company_id: employee.company_id,
      employee_id: employee.employee_id || '',
      name: employee.name,
      email: employee.email || '',
      phone: employee.phone || '',
      department: employee.department || '',
      designation: employee.designation || '',
      location: employee.location || ''
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingEmployee(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_id || !formData.name) {
      toast.error('Company and Name are required');
      return;
    }

    const submitData = { ...formData };
    // Clean up optional fields
    ['employee_id', 'email', 'phone', 'department', 'designation', 'location'].forEach(field => {
      if (!submitData[field]) delete submitData[field];
    });

    try {
      if (editingEmployee) {
        await axios.put(`${API}/admin/company-employees/${editingEmployee.id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Employee updated');
      } else {
        await axios.post(`${API}/admin/company-employees`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Employee created');
      }
      fetchData();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (employee) => {
    if (!window.confirm(`Remove "${employee.name}" from employees list?`)) return;
    
    try {
      await axios.delete(`${API}/admin/company-employees/${employee.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Employee removed');
      fetchData();
    } catch (error) {
      toast.error('Failed to remove employee');
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get(`${API}/admin/company-employees/template/download`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'employee_import_template.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Template downloaded');
    } catch (error) {
      toast.error('Failed to download template');
    }
  };

  const handleBulkUpload = async () => {
    if (!uploadFile) {
      toast.error('Please select a file');
      return;
    }

    setUploading(true);
    setUploadResults(null);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      
      const response = await axios.post(`${API}/admin/company-employees/bulk-import`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setUploadResults(response.data);
      if (response.data.created > 0) {
        toast.success(`Successfully imported ${response.data.created} employees`);
        fetchData();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Import failed');
    } finally {
      setUploading(false);
    }
  };

  const closeBulkUpload = () => {
    setBulkUploadOpen(false);
    setUploadFile(null);
    setUploadResults(null);
  };

  const filtered = employees.filter(e => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      if (!e.name?.toLowerCase().includes(q) && 
          !e.email?.toLowerCase().includes(q) &&
          !e.department?.toLowerCase().includes(q) &&
          !e.employee_id?.toLowerCase().includes(q)) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Company Employees</h1>
          <p className="text-slate-500 mt-1">Manage employees who can be assigned to devices</p>
        </div>
        <div className="flex gap-3">
          <Button 
            variant="outline" 
            onClick={() => setBulkUploadOpen(true)}
            data-testid="bulk-upload-btn"
          >
            <Upload className="h-4 w-4 mr-2" />
            Bulk Import
          </Button>
          <Button 
            onClick={openCreateModal} 
            className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
            data-testid="add-employee-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Employee
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name, email, department..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input pl-10"
            data-testid="employee-search-input"
          />
        </div>
        <select
          value={filterCompany}
          onChange={(e) => setFilterCompany(e.target.value)}
          className="form-select w-64"
          data-testid="employee-company-filter"
        >
          <option value="">All Companies</option>
          {companies.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Users className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{employees.length}</p>
              <p className="text-sm text-slate-500">Total Employees</p>
            </div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Building2 className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">
                {new Set(employees.map(e => e.company_id)).size}
              </p>
              <p className="text-sm text-slate-500">Companies</p>
            </div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <User className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">
                {new Set(employees.map(e => e.department).filter(Boolean)).size}
              </p>
              <p className="text-sm text-slate-500">Departments</p>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : filtered.length > 0 ? (
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Employee</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Company</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Department</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Contact</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Location</th>
                <th className="w-10"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((employee) => (
                <tr key={employee.id} className="hover:bg-slate-50" data-testid={`employee-row-${employee.id}`}>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-sm font-medium">
                        {employee.name?.charAt(0)?.toUpperCase() || '?'}
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{employee.name}</p>
                        {employee.employee_id && (
                          <p className="text-xs text-slate-500">ID: {employee.employee_id}</p>
                        )}
                        {employee.designation && (
                          <p className="text-xs text-slate-500">{employee.designation}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-slate-600">{employee.company_name || getCompanyName(employee.company_id)}</span>
                  </td>
                  <td className="px-4 py-3">
                    {employee.department ? (
                      <span className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-700">
                        {employee.department}
                      </span>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm">
                      {employee.email && <p className="text-slate-600">{employee.email}</p>}
                      {employee.phone && <p className="text-slate-500 text-xs">{employee.phone}</p>}
                      {!employee.email && !employee.phone && <span className="text-slate-400">-</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-slate-600">{employee.location || '-'}</span>
                  </td>
                  <td className="px-4 py-3">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className="p-1.5 hover:bg-slate-100 rounded-lg" data-testid={`employee-actions-${employee.id}`}>
                          <MoreVertical className="h-4 w-4 text-slate-400" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openEditModal(employee)}>
                          <Edit2 className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600" onClick={() => handleDelete(employee)}>
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
        ) : (
          <div className="text-center py-16">
            <Users className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No employees found</p>
            <Button onClick={openCreateModal} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add your first employee
            </Button>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingEmployee ? 'Edit Employee' : 'Add Employee'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Company *</label>
              <SmartSelect
                value={formData.company_id}
                onValueChange={(value) => setFormData({ ...formData, company_id: value })}
                placeholder="Select Company"
                searchPlaceholder="Search companies..."
                emptyText="No companies found"
                fetchOptions={async (q) => {
                  const res = await axios.get(`${API}/admin/companies`, {
                    params: { q, limit: 20 },
                    headers: { Authorization: `Bearer ${token}` }
                  });
                  return res.data;
                }}
                displayKey="name"
                valueKey="id"
                allowCreate
                createLabel="Add New Company"
                renderCreateForm={({ initialValue, onSuccess, onCancel }) => (
                  <QuickCreateCompany
                    initialValue={initialValue}
                    onSuccess={onSuccess}
                    onCancel={onCancel}
                    token={token}
                  />
                )}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Full Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="form-input"
                  placeholder="John Smith"
                  data-testid="employee-name-input"
                />
              </div>
              <div>
                <label className="form-label">Employee ID</label>
                <input
                  type="text"
                  value={formData.employee_id}
                  onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                  className="form-input"
                  placeholder="EMP001 (optional)"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="form-input"
                  placeholder="john@company.com"
                />
              </div>
              <div>
                <label className="form-label">Phone</label>
                <input
                  type="text"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="form-input"
                  placeholder="+91 98765 43210"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Department</label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  className="form-input"
                  placeholder="IT, HR, Sales..."
                />
              </div>
              <div>
                <label className="form-label">Designation</label>
                <input
                  type="text"
                  value={formData.designation}
                  onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                  className="form-input"
                  placeholder="Software Engineer..."
                />
              </div>
            </div>
            
            <div>
              <label className="form-label">Location</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="form-input"
                placeholder="Floor 2, Desk 15..."
              />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="employee-submit-btn">
                {editingEmployee ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Bulk Upload Modal */}
      <Dialog open={bulkUploadOpen} onOpenChange={closeBulkUpload}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Bulk Import Employees</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-sm text-slate-600">
              Upload a CSV or Excel file with employee data. Download the template to see the required format.
            </p>
            
            <Button variant="outline" onClick={handleDownloadTemplate} className="w-full">
              <Download className="h-4 w-4 mr-2" />
              Download CSV Template
            </Button>
            
            <div className="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="hidden"
                id="employee-file-upload"
              />
              <label htmlFor="employee-file-upload" className="cursor-pointer">
                <Upload className="h-8 w-8 mx-auto text-slate-400 mb-2" />
                <p className="text-sm text-slate-600">
                  {uploadFile ? uploadFile.name : 'Click to select file or drag and drop'}
                </p>
                <p className="text-xs text-slate-400 mt-1">CSV or Excel files only</p>
              </label>
            </div>
            
            {uploadResults && (
              <div className={`p-4 rounded-lg ${uploadResults.errors?.length > 0 ? 'bg-amber-50 border border-amber-200' : 'bg-emerald-50 border border-emerald-200'}`}>
                <p className="font-medium text-sm">
                  ✅ Created: {uploadResults.created} employees
                </p>
                {uploadResults.errors?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium text-amber-700">Errors ({uploadResults.errors.length}):</p>
                    <ul className="text-xs text-amber-600 mt-1 max-h-32 overflow-y-auto">
                      {uploadResults.errors.slice(0, 10).map((err, i) => (
                        <li key={i}>Row {err.row}: {err.error}</li>
                      ))}
                      {uploadResults.errors.length > 10 && (
                        <li>...and {uploadResults.errors.length - 10} more</li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}
            
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={closeBulkUpload}>
                Close
              </Button>
              <Button 
                onClick={handleBulkUpload} 
                disabled={!uploadFile || uploading}
                className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
              >
                {uploading ? 'Importing...' : 'Import'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Employees;
