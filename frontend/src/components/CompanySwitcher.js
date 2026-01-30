import { useState, useEffect, useRef } from 'react';
import { Building2, ChevronDown, Check, Users, Search, X } from 'lucide-react';
import { cn } from '../lib/utils';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * Company Switcher Component
 * Allows MSP technicians and admins to switch between assigned companies.
 * MSP Admins can see all companies, MSP Technicians see only assigned ones.
 */
export default function CompanySwitcher({ className }) {
  const [isOpen, setIsOpen] = useState(false);
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [userRole, setUserRole] = useState(null);
  const dropdownRef = useRef(null);
  
  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchCompanies();
    fetchUserRole();
    
    // Load saved company from session
    const savedCompanyId = sessionStorage.getItem('selectedCompanyId');
    if (savedCompanyId) {
      const savedCompany = companies.find(c => c.id === savedCompanyId);
      if (savedCompany) {
        setSelectedCompany(savedCompany);
      }
    }
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchCompanies = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    
    try {
      const response = await axios.get(`${API}/api/admin/companies`, { headers });
      setCompanies(response.data || []);
      
      // Auto-select first company if none selected
      const savedCompanyId = sessionStorage.getItem('selectedCompanyId');
      if (savedCompanyId && response.data) {
        const found = response.data.find(c => c.id === savedCompanyId);
        if (found) setSelectedCompany(found);
      }
    } catch (error) {
      console.error('Failed to fetch companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserRole = async () => {
    if (!token) return;
    
    try {
      const response = await axios.get(`${API}/api/auth/me`, { headers });
      setUserRole(response.data.org_role || response.data.role);
    } catch (error) {
      console.error('Failed to fetch user role');
    }
  };

  const handleSelectCompany = (company) => {
    setSelectedCompany(company);
    sessionStorage.setItem('selectedCompanyId', company.id);
    sessionStorage.setItem('selectedCompanyName', company.name);
    setIsOpen(false);
    setSearchQuery('');
    
    // Dispatch custom event so other components can react
    window.dispatchEvent(new CustomEvent('companyChanged', { 
      detail: { companyId: company.id, companyName: company.name }
    }));
    
    // Reload the page to apply the company filter
    // This ensures all data is fetched for the selected company
    window.location.reload();
  };

  const handleClearSelection = (e) => {
    e.stopPropagation();
    setSelectedCompany(null);
    sessionStorage.removeItem('selectedCompanyId');
    sessionStorage.removeItem('selectedCompanyName');
    
    window.dispatchEvent(new CustomEvent('companyChanged', { 
      detail: { companyId: null, companyName: null }
    }));
    
    window.location.reload();
  };

  const filteredCompanies = companies.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Only show for MSP roles (msp_admin, msp_technician, owner, admin)
  const canSwitchCompanies = ['msp_admin', 'msp_technician', 'owner', 'admin'].includes(userRole);
  
  if (!canSwitchCompanies || companies.length === 0) {
    return null;
  }

  return (
    <div className={cn("relative", className)} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
          "border border-slate-200 hover:border-slate-300 hover:bg-slate-50",
          isOpen && "border-blue-300 bg-blue-50/50",
          selectedCompany ? "bg-blue-50/30" : "bg-white"
        )}
        data-testid="company-switcher-btn"
      >
        <div className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
          selectedCompany ? "bg-blue-100" : "bg-slate-100"
        )}>
          <Building2 className={cn(
            "w-4 h-4",
            selectedCompany ? "text-blue-600" : "text-slate-500"
          )} />
        </div>
        
        <div className="flex-1 text-left min-w-0">
          {selectedCompany ? (
            <>
              <p className="text-sm font-medium text-slate-900 truncate">
                {selectedCompany.name}
              </p>
              <p className="text-xs text-slate-500">
                Viewing company data
              </p>
            </>
          ) : (
            <>
              <p className="text-sm font-medium text-slate-600">
                All Companies
              </p>
              <p className="text-xs text-slate-400">
                {companies.length} companies
              </p>
            </>
          )}
        </div>
        
        <div className="flex items-center gap-1">
          {selectedCompany && (
            <button
              onClick={handleClearSelection}
              className="p-1 hover:bg-slate-200 rounded transition-colors"
              title="Clear selection"
            >
              <X className="w-3.5 h-3.5 text-slate-400" />
            </button>
          )}
          <ChevronDown className={cn(
            "w-4 h-4 text-slate-400 transition-transform",
            isOpen && "rotate-180"
          )} />
        </div>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-lg border border-slate-200 z-50 overflow-hidden">
          {/* Search */}
          {companies.length > 5 && (
            <div className="p-2 border-b border-slate-100">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search companies..."
                  className="w-full pl-8 pr-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  autoFocus
                />
              </div>
            </div>
          )}
          
          {/* Companies List */}
          <div className="max-h-64 overflow-y-auto">
            {/* All Companies option */}
            <button
              onClick={() => {
                setSelectedCompany(null);
                sessionStorage.removeItem('selectedCompanyId');
                sessionStorage.removeItem('selectedCompanyName');
                setIsOpen(false);
                window.location.reload();
              }}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 hover:bg-slate-50 transition-colors",
                !selectedCompany && "bg-blue-50"
              )}
            >
              <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                <Users className="w-4 h-4 text-slate-500" />
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-medium text-slate-700">All Companies</p>
                <p className="text-xs text-slate-500">{companies.length} total</p>
              </div>
              {!selectedCompany && (
                <Check className="w-4 h-4 text-blue-600" />
              )}
            </button>
            
            {/* Divider */}
            <div className="border-t border-slate-100" />
            
            {/* Company options */}
            {loading ? (
              <div className="p-4 text-center text-sm text-slate-500">
                Loading companies...
              </div>
            ) : filteredCompanies.length === 0 ? (
              <div className="p-4 text-center text-sm text-slate-500">
                No companies found
              </div>
            ) : (
              filteredCompanies.map((company) => (
                <button
                  key={company.id}
                  onClick={() => handleSelectCompany(company)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 hover:bg-slate-50 transition-colors",
                    selectedCompany?.id === company.id && "bg-blue-50"
                  )}
                  data-testid={`company-option-${company.id}`}
                >
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium",
                    selectedCompany?.id === company.id 
                      ? "bg-blue-100 text-blue-700"
                      : "bg-slate-100 text-slate-600"
                  )}>
                    {company.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 text-left min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {company.name}
                    </p>
                    {company.email && (
                      <p className="text-xs text-slate-500 truncate">
                        {company.email}
                      </p>
                    )}
                  </div>
                  {selectedCompany?.id === company.id && (
                    <Check className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
