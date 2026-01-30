import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';
import { 
  Users, Plus, Edit, Trash2, Shield, X, Loader2, CheckCircle,
  Crown, UserCog, Eye
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const ROLE_BADGES = {
  platform_owner: { label: 'Owner', class: 'bg-amber-500/20 text-amber-400 border-amber-500/30', icon: Crown },
  platform_admin: { label: 'Admin', class: 'bg-purple-500/20 text-purple-400 border-purple-500/30', icon: Shield },
  support: { label: 'Support', class: 'bg-blue-500/20 text-blue-400 border-blue-500/30', icon: UserCog }
};

export default function PlatformAdmins() {
  const [admins, setAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [currentAdmin, setCurrentAdmin] = useState(null);
  
  const token = localStorage.getItem('platformToken');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchAdmins();
  }, []);

  const fetchAdmins = async () => {
    try {
      const response = await axios.get(`${API}/api/platform/admins`, { headers });
      setAdmins(response.data);
    } catch (error) {
      toast.error('Failed to load admins');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (adminId) => {
    if (!window.confirm('Are you sure you want to delete this admin?')) return;
    
    try {
      await axios.delete(`${API}/api/platform/admins/${adminId}`, { headers });
      toast.success('Admin deleted');
      fetchAdmins();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete admin');
    }
  };

  return (
    <div className="space-y-6" data-testid="platform-admins">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Platform Admins</h1>
          <p className="text-slate-400">Manage super admin users with platform access</p>
        </div>
        <Button 
          onClick={() => { setCurrentAdmin(null); setShowModal(true); }}
          className="bg-purple-600 hover:bg-purple-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Admin
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/20">
                <Crown className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {admins.filter(a => a.role === 'platform_owner').length}
                </p>
                <p className="text-sm text-slate-400">Owners</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Shield className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {admins.filter(a => a.role === 'platform_admin').length}
                </p>
                <p className="text-sm text-slate-400">Admins</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Users className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{admins.length}</p>
                <p className="text-sm text-slate-400">Total Admins</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Admins List */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            All Platform Admins
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
            </div>
          ) : admins.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              No platform admins found
            </div>
          ) : (
            <div className="space-y-3">
              {admins.map(admin => {
                const roleConfig = ROLE_BADGES[admin.role] || ROLE_BADGES.platform_admin;
                const RoleIcon = roleConfig.icon;
                
                return (
                  <div 
                    key={admin.id} 
                    className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                        <span className="text-lg font-semibold text-purple-400">
                          {admin.name?.charAt(0)?.toUpperCase() || 'A'}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-white">{admin.name}</p>
                        <p className="text-sm text-slate-400">{admin.email}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${roleConfig.class}`}>
                        <RoleIcon className="w-3.5 h-3.5" />
                        {roleConfig.label}
                      </span>
                      
                      <div className="text-sm text-slate-400">
                        {admin.last_login ? (
                          <span>Last login: {new Date(admin.last_login).toLocaleDateString()}</span>
                        ) : (
                          <span>Never logged in</span>
                        )}
                      </div>
                      
                      {admin.role !== 'platform_owner' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(admin.id)}
                          className="text-red-400 hover:text-red-300 hover:bg-red-500/20"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Admin Modal */}
      {showModal && (
        <CreateAdminModal
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            fetchAdmins();
          }}
          token={token}
        />
      )}
    </div>
  );
}

function CreateAdminModal({ onClose, onSuccess, token }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'platform_admin'
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/api/platform/admins`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Admin created successfully');
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create admin');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white">Add Platform Admin</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Full Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
              placeholder="John Doe"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
              placeholder="admin@platform.com"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
              placeholder="••••••••"
              required
              minLength={8}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Role</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            >
              <option value="platform_admin">Platform Admin</option>
              <option value="support">Support</option>
            </select>
          </div>
          
          <div className="flex gap-3 pt-4">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1 border-slate-600">
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="flex-1 bg-purple-600 hover:bg-purple-700">
              {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
              Create Admin
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
