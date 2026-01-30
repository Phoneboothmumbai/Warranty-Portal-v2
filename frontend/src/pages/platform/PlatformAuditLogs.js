import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';
import { 
  ScrollText, Search, Filter, RefreshCw, Loader2, 
  User, Building2, Settings, Shield, AlertCircle,
  ChevronLeft, ChevronRight, Eye
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const ACTION_COLORS = {
  create_organization: 'bg-emerald-500/20 text-emerald-400',
  update_organization: 'bg-blue-500/20 text-blue-400',
  suspend_organization: 'bg-amber-500/20 text-amber-400',
  reactivate_organization: 'bg-purple-500/20 text-purple-400',
  delete_organization: 'bg-red-500/20 text-red-400',
  create_platform_admin: 'bg-emerald-500/20 text-emerald-400',
  update_platform_settings: 'bg-blue-500/20 text-blue-400',
  default: 'bg-slate-500/20 text-slate-400'
};

const ACTION_ICONS = {
  create_organization: Building2,
  update_organization: Building2,
  suspend_organization: AlertCircle,
  reactivate_organization: Building2,
  delete_organization: Building2,
  create_platform_admin: Shield,
  update_platform_settings: Settings,
  default: ScrollText
};

export default function PlatformAuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });
  const [filters, setFilters] = useState({
    action: '',
    entity_type: ''
  });
  const [selectedLog, setSelectedLog] = useState(null);
  
  const token = localStorage.getItem('platformToken');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchLogs();
  }, [pagination.page, filters]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', pagination.page);
      params.append('limit', 20);
      if (filters.action) params.append('action', filters.action);
      if (filters.entity_type) params.append('entity_type', filters.entity_type);
      
      const response = await axios.get(`${API}/api/platform/audit-logs?${params}`, { headers });
      setLogs(response.data.logs || []);
      setPagination(prev => ({
        ...prev,
        pages: response.data.pages || 1,
        total: response.data.total || 0
      }));
    } catch (error) {
      toast.error('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const formatAction = (action) => {
    return action.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  const getActionIcon = (action) => {
    return ACTION_ICONS[action] || ACTION_ICONS.default;
  };

  const getActionColor = (action) => {
    return ACTION_COLORS[action] || ACTION_COLORS.default;
  };

  return (
    <div className="space-y-6" data-testid="platform-audit-logs">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Audit Logs</h1>
          <p className="text-slate-400">Track all platform administrative actions</p>
        </div>
        <Button onClick={fetchLogs} variant="outline" className="border-slate-600 text-slate-300">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={filters.action}
          onChange={(e) => {
            setFilters({ ...filters, action: e.target.value });
            setPagination(prev => ({ ...prev, page: 1 }));
          }}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
        >
          <option value="">All Actions</option>
          <option value="create_organization">Create Organization</option>
          <option value="update_organization">Update Organization</option>
          <option value="suspend_organization">Suspend Organization</option>
          <option value="reactivate_organization">Reactivate Organization</option>
          <option value="delete_organization">Delete Organization</option>
          <option value="create_platform_admin">Create Platform Admin</option>
          <option value="update_platform_settings">Update Platform Settings</option>
        </select>
        
        <select
          value={filters.entity_type}
          onChange={(e) => {
            setFilters({ ...filters, entity_type: e.target.value });
            setPagination(prev => ({ ...prev, page: 1 }));
          }}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
        >
          <option value="">All Entity Types</option>
          <option value="organization">Organization</option>
          <option value="platform_admin">Platform Admin</option>
          <option value="platform_settings">Platform Settings</option>
        </select>
      </div>

      {/* Logs List */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <ScrollText className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No audit logs found</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-700">
              {logs.map(log => {
                const ActionIcon = getActionIcon(log.action);
                
                return (
                  <div 
                    key={log.id} 
                    className="p-4 hover:bg-slate-700/30 transition-colors cursor-pointer"
                    onClick={() => setSelectedLog(log)}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-lg ${getActionColor(log.action)}`}>
                        <ActionIcon className="w-5 h-5" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getActionColor(log.action)}`}>
                            {formatAction(log.action)}
                          </span>
                          <span className="text-slate-500 text-sm">on</span>
                          <span className="text-slate-300 text-sm font-mono">{log.entity_type}</span>
                        </div>
                        
                        <p className="text-white font-medium">
                          {log.performed_by_name || log.performed_by_email || 'Unknown'}
                        </p>
                        
                        <p className="text-sm text-slate-400">
                          Entity ID: <span className="font-mono">{log.entity_id?.slice(0, 8)}...</span>
                        </p>
                      </div>
                      
                      <div className="text-right">
                        <p className="text-sm text-slate-400">
                          {new Date(log.created_at).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-slate-500">
                          {new Date(log.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                      
                      <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          
          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-700">
              <p className="text-sm text-slate-400">
                Page {pagination.page} of {pagination.pages} ({pagination.total} total)
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.page === 1}
                  onClick={() => setPagination(p => ({ ...p, page: p.page - 1 }))}
                  className="border-slate-600 text-slate-300"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.page === pagination.pages}
                  onClick={() => setPagination(p => ({ ...p, page: p.page + 1 }))}
                  className="border-slate-600 text-slate-300"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setSelectedLog(null)}>
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <h2 className="text-xl font-semibold text-white">Audit Log Details</h2>
              <button onClick={() => setSelectedLog(null)} className="text-slate-400 hover:text-white">
                ×
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="text-sm text-slate-400">Action</label>
                <p className="text-white font-medium">{formatAction(selectedLog.action)}</p>
              </div>
              
              <div>
                <label className="text-sm text-slate-400">Entity Type</label>
                <p className="text-white font-mono">{selectedLog.entity_type}</p>
              </div>
              
              <div>
                <label className="text-sm text-slate-400">Entity ID</label>
                <p className="text-white font-mono text-sm break-all">{selectedLog.entity_id}</p>
              </div>
              
              <div>
                <label className="text-sm text-slate-400">Performed By</label>
                <p className="text-white">{selectedLog.performed_by_name || 'Unknown'}</p>
                <p className="text-slate-400 text-sm">{selectedLog.performed_by_email}</p>
              </div>
              
              <div>
                <label className="text-sm text-slate-400">Timestamp</label>
                <p className="text-white">{new Date(selectedLog.created_at).toLocaleString()}</p>
              </div>
              
              {selectedLog.ip_address && (
                <div>
                  <label className="text-sm text-slate-400">IP Address</label>
                  <p className="text-white font-mono">{selectedLog.ip_address}</p>
                </div>
              )}
              
              {selectedLog.changes && Object.keys(selectedLog.changes).length > 0 && (
                <div>
                  <label className="text-sm text-slate-400">Changes</label>
                  <pre className="mt-2 p-3 bg-slate-900 rounded-lg text-sm text-slate-300 overflow-auto max-h-48">
                    {JSON.stringify(selectedLog.changes, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
