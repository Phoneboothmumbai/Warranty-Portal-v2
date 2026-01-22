import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  Search, Key, Eye, EyeOff, Copy, Check, Laptop, Wifi, 
  Camera, Server, Router, Lock, Globe, Shield, MapPin,
  ExternalLink, Phone, User
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Device type icons
const deviceTypeIcons = {
  'CCTV': Camera,
  'NVR': Camera,
  'DVR': Camera,
  'Router': Router,
  'Access Point': Wifi,
  'Switch': Server,
  'Server': Server,
  'Firewall': Shield,
  'broadband': Globe,
  'leased_line': Globe,
  'fiber': Globe,
  'default': Laptop
};

const CompanyCredentials = () => {
  const { token } = useCompanyAuth();
  const [credentials, setCredentials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [visiblePasswords, setVisiblePasswords] = useState({});
  const [copiedField, setCopiedField] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/company/credentials`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCredentials(response.data);
    } catch (error) {
      toast.error('Failed to load credentials');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredCredentials = credentials.filter(cred => {
    const matchesType = filterType === 'all' || cred.source_type === filterType;
    const matchesSearch = !searchQuery || 
      cred.source_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cred.device_type?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cred.serial_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cred.location?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const togglePasswordVisibility = (id, field) => {
    const key = `${id}-${field}`;
    setVisiblePasswords(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const copyToClipboard = async (text, id, field) => {
    try {
      await navigator.clipboard.writeText(text);
      const key = `${id}-${field}`;
      setCopiedField(key);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      toast.error('Failed to copy');
    }
  };

  const openDetail = (item) => {
    setSelectedItem(item);
    setDetailModalOpen(true);
  };

  const getIcon = (item) => {
    const type = item.device_type || '';
    const Icon = deviceTypeIcons[type] || deviceTypeIcons['default'];
    return Icon;
  };

  const renderCredentialValue = (value, id, field, isPassword = false) => {
    if (!value) return <span className="text-slate-400">-</span>;
    
    const key = `${id}-${field}`;
    const isVisible = visiblePasswords[key];
    const isCopied = copiedField === key;

    return (
      <div className="flex items-center gap-2">
        <code className={`text-sm ${isPassword ? 'font-mono' : ''} bg-slate-100 px-2 py-1 rounded`}>
          {isPassword && !isVisible ? '••••••••' : value}
        </code>
        {isPassword && (
          <button
            onClick={(e) => { e.stopPropagation(); togglePasswordVisibility(id, field); }}
            className="p-1 hover:bg-slate-100 rounded"
          >
            {isVisible ? <EyeOff className="h-4 w-4 text-slate-400" /> : <Eye className="h-4 w-4 text-slate-400" />}
          </button>
        )}
        <button
          onClick={(e) => { e.stopPropagation(); copyToClipboard(value, id, field); }}
          className="p-1 hover:bg-slate-100 rounded"
        >
          {isCopied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4 text-slate-400" />}
        </button>
      </div>
    );
  };

  const stats = {
    total: credentials.length,
    devices: credentials.filter(c => c.source_type === 'device').length,
    internet: credentials.filter(c => c.source_type === 'internet').length
  };

  return (
    <div className="space-y-6" data-testid="company-credentials-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 flex items-center gap-2">
          <Key className="h-6 w-6 text-amber-600" />
          Credentials
        </h1>
        <p className="text-slate-500">View all your device and network credentials in one place</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Key className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              <p className="text-xs text-slate-500">Total Credentials</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Laptop className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.devices}</p>
              <p className="text-xs text-slate-500">Device Credentials</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Globe className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.internet}</p>
              <p className="text-xs text-slate-500">Internet/ISP</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-100 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by device, type, location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input pl-10"
            />
          </div>
          <select 
            value={filterType} 
            onChange={(e) => setFilterType(e.target.value)} 
            className="form-select w-40"
          >
            <option value="all">All Types</option>
            <option value="device">Devices</option>
            <option value="internet">Internet/ISP</option>
          </select>
        </div>
      </div>

      {/* Credentials Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-amber-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : filteredCredentials.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredCredentials.map((item) => {
            const Icon = getIcon(item);
            const isInternet = item.source_type === 'internet';
            
            return (
              <div 
                key={`${item.source_type}-${item.id}`}
                className="bg-white rounded-xl border border-slate-100 p-5 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => openDetail(item)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      isInternet ? 'bg-emerald-100' : 'bg-blue-100'
                    }`}>
                      <Icon className={`h-6 w-6 ${isInternet ? 'text-emerald-600' : 'text-blue-600'}`} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{item.source_name}</h3>
                      {item.location && (
                        <p className="text-sm text-slate-500 flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {item.location}
                        </p>
                      )}
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    isInternet ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {isInternet ? 'Internet' : item.device_type}
                  </span>
                </div>

                {/* Quick credential preview */}
                <div className="space-y-2 text-sm">
                  {isInternet ? (
                    <>
                      {item.credentials?.wifi_ssid && (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">WiFi SSID:</span>
                          <code className="bg-slate-100 px-2 py-0.5 rounded">{item.credentials.wifi_ssid}</code>
                        </div>
                      )}
                      {item.credentials?.router_ip && (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Router IP:</span>
                          <code className="bg-slate-100 px-2 py-0.5 rounded">{item.credentials.router_ip}</code>
                        </div>
                      )}
                      {item.plan_name && (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Plan:</span>
                          <span className="text-slate-700">{item.plan_name}</span>
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      {item.credentials?.ip_address && (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">IP Address:</span>
                          <code className="bg-slate-100 px-2 py-0.5 rounded">{item.credentials.ip_address}</code>
                        </div>
                      )}
                      {item.credentials?.login_url && (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Login URL:</span>
                          <code className="bg-slate-100 px-2 py-0.5 rounded text-xs truncate max-w-[200px]">{item.credentials.login_url}</code>
                        </div>
                      )}
                      {item.assigned_to && (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Assigned To:</span>
                          <span className="text-slate-700 flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {item.assigned_to}
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                  <span>{item.serial_number || item.asset_tag || ''}</span>
                  <span className="flex items-center gap-1">
                    <Lock className="h-3 w-3" />
                    Click for full details
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-100 p-12 text-center">
          <Key className="h-12 w-12 mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500">No credentials found</p>
          <p className="text-sm text-slate-400 mt-1">Contact your administrator to add credentials for your devices</p>
        </div>
      )}

      {/* Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="h-5 w-5 text-amber-600" />
              Credential Details
            </DialogTitle>
          </DialogHeader>
          {selectedItem && (
            <div className="space-y-6 mt-4">
              {/* Header Info */}
              <div className="flex items-start gap-4 p-4 bg-slate-50 rounded-lg">
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                  selectedItem.source_type === 'internet' ? 'bg-emerald-100' : 'bg-blue-100'
                }`}>
                  {(() => { const Icon = getIcon(selectedItem); return <Icon className={`h-7 w-7 ${selectedItem.source_type === 'internet' ? 'text-emerald-600' : 'text-blue-600'}`} />; })()}
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold">{selectedItem.source_name}</h3>
                  {selectedItem.location && <p className="text-slate-500">{selectedItem.location}</p>}
                  <div className="flex gap-4 mt-2 text-sm text-slate-500">
                    {selectedItem.device_type && <span>Type: {selectedItem.device_type}</span>}
                    {selectedItem.serial_number && <span>SN: {selectedItem.serial_number}</span>}
                  </div>
                </div>
              </div>

              {/* Credentials Section */}
              <div>
                <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Access Credentials
                </h4>
                <div className="space-y-3">
                  {selectedItem.source_type === 'internet' ? (
                    <>
                      {selectedItem.credentials?.router_ip && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">Router IP</span>
                          {renderCredentialValue(selectedItem.credentials.router_ip, selectedItem.id, 'router_ip')}
                        </div>
                      )}
                      {selectedItem.credentials?.router_username && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">Router Username</span>
                          {renderCredentialValue(selectedItem.credentials.router_username, selectedItem.id, 'router_username')}
                        </div>
                      )}
                      {selectedItem.credentials?.router_password && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">Router Password</span>
                          {renderCredentialValue(selectedItem.credentials.router_password, selectedItem.id, 'router_password', true)}
                        </div>
                      )}
                      {selectedItem.credentials?.wifi_ssid && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">WiFi SSID</span>
                          {renderCredentialValue(selectedItem.credentials.wifi_ssid, selectedItem.id, 'wifi_ssid')}
                        </div>
                      )}
                      {selectedItem.credentials?.wifi_password && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">WiFi Password</span>
                          {renderCredentialValue(selectedItem.credentials.wifi_password, selectedItem.id, 'wifi_password', true)}
                        </div>
                      )}
                      {selectedItem.credentials?.static_ip && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">Static IP</span>
                          {renderCredentialValue(selectedItem.credentials.static_ip, selectedItem.id, 'static_ip')}
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      {selectedItem.credentials?.ip_address && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">IP Address</span>
                          {renderCredentialValue(selectedItem.credentials.ip_address, selectedItem.id, 'ip_address')}
                        </div>
                      )}
                      {selectedItem.credentials?.port && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">Port</span>
                          {renderCredentialValue(selectedItem.credentials.port, selectedItem.id, 'port')}
                        </div>
                      )}
                      {selectedItem.credentials?.login_url && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">Login URL</span>
                          <div className="flex items-center gap-2">
                            {renderCredentialValue(selectedItem.credentials.login_url, selectedItem.id, 'login_url')}
                            <a href={selectedItem.credentials.login_url} target="_blank" rel="noopener noreferrer" className="p-1 hover:bg-slate-200 rounded">
                              <ExternalLink className="h-4 w-4 text-blue-500" />
                            </a>
                          </div>
                        </div>
                      )}
                      {selectedItem.credentials?.username && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">Username</span>
                          {renderCredentialValue(selectedItem.credentials.username, selectedItem.id, 'username')}
                        </div>
                      )}
                      {selectedItem.credentials?.password && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">Password</span>
                          {renderCredentialValue(selectedItem.credentials.password, selectedItem.id, 'password', true)}
                        </div>
                      )}
                      {selectedItem.credentials?.app_url && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">App URL</span>
                          <div className="flex items-center gap-2">
                            {renderCredentialValue(selectedItem.credentials.app_url, selectedItem.id, 'app_url')}
                            <a href={selectedItem.credentials.app_url} target="_blank" rel="noopener noreferrer" className="p-1 hover:bg-slate-200 rounded">
                              <ExternalLink className="h-4 w-4 text-blue-500" />
                            </a>
                          </div>
                        </div>
                      )}
                      {selectedItem.credentials?.wifi_ssid && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">WiFi SSID</span>
                          {renderCredentialValue(selectedItem.credentials.wifi_ssid, selectedItem.id, 'wifi_ssid')}
                        </div>
                      )}
                      {selectedItem.credentials?.wifi_password && (
                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600">WiFi Password</span>
                          {renderCredentialValue(selectedItem.credentials.wifi_password, selectedItem.id, 'wifi_password', true)}
                        </div>
                      )}
                      {selectedItem.credentials?.notes && (
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <span className="text-slate-600 block mb-1">Access Notes</span>
                          <p className="text-sm text-slate-700 whitespace-pre-wrap">{selectedItem.credentials.notes}</p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>

              {/* Support Contact for Internet */}
              {selectedItem.source_type === 'internet' && selectedItem.support_phone && (
                <div>
                  <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    Support Contact
                  </h4>
                  <div className="p-3 bg-slate-50 rounded-lg flex items-center gap-2">
                    <Phone className="h-4 w-4 text-slate-400" />
                    <a href={`tel:${selectedItem.support_phone}`} className="text-blue-600 hover:underline">
                      {selectedItem.support_phone}
                    </a>
                  </div>
                </div>
              )}

              <div className="flex justify-end pt-4">
                <Button variant="outline" onClick={() => setDetailModalOpen(false)}>
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CompanyCredentials;
