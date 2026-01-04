import { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, Search, Mail, Phone, Shield, User } from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyUsers = () => {
  const { token, isAdmin } = useCompanyAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/company/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user =>
    user.name?.toLowerCase().includes(search.toLowerCase()) ||
    user.email?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-users-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Users / Contacts</h1>
        <p className="text-slate-500 mt-1">View company users and contact persons</p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search users..."
            className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            data-testid="user-search-input"
          />
        </div>
      </div>

      {/* User List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {filteredUsers.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {filteredUsers.map((user) => (
              <div 
                key={user.id} 
                className="p-4 hover:bg-slate-50 transition-colors"
                data-testid={`user-row-${user.id}`}
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                    <span className="text-lg font-semibold text-emerald-700">
                      {user.name?.charAt(0)?.toUpperCase() || 'U'}
                    </span>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-slate-900">{user.name}</h3>
                      {user.role === 'company_admin' && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-emerald-50 text-emerald-700 text-xs rounded-full">
                          <Shield className="h-3 w-3" />
                          Admin
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-sm text-slate-500">
                      {user.email && (
                        <span className="flex items-center gap-1">
                          <Mail className="h-3.5 w-3.5" />
                          {user.email}
                        </span>
                      )}
                      {user.phone && (
                        <span className="flex items-center gap-1">
                          <Phone className="h-3.5 w-3.5" />
                          {user.phone}
                        </span>
                      )}
                    </div>
                    {user.designation && (
                      <p className="text-xs text-slate-400 mt-1">{user.designation}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <Users className="h-12 w-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500">No users found</p>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="text-sm text-slate-500 text-center">
        {filteredUsers.length} user{filteredUsers.length !== 1 ? 's' : ''} found
      </div>
    </div>
  );
};

export default CompanyUsers;
