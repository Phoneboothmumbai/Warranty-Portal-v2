import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { 
  Settings, RefreshCw, Monitor, Server, Wifi, WifiOff,
  Play, RotateCcw, CheckCircle, XCircle, AlertTriangle,
  ExternalLink, Loader2, Download, Building2, Laptop
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const WatchTowerIntegration = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState([]);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [showSetup, setShowSetup] = useState(false);
  const [setupForm, setSetupForm] = useState({
    api_url: '',
    api_key: ''
  });
  const [downloadingFor, setDownloadingFor] = useState(null);
  const [agentDownloadUrl, setAgentDownloadUrl] = useState(null);
  
  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchConfig();
    fetchCompanies();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${API}/api/watchtower/config`, { headers });
      setConfig(res.data);
      if (res.data.configured && res.data.enabled) {
        fetchAgents();
      }
    } catch (error) {
      toast.error('Failed to load WatchTower configuration');
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanies = async () => {
    try {
      const res = await axios.get(`${API}/api/admin/companies?limit=100`, { headers });
      setCompanies(res.data);
      if (res.data.length > 0) {
        setSelectedCompany(res.data[0].id);
      }
    } catch (error) {
      console.error('Failed to load companies');
    }
  };

  const fetchAgents = async () => {
    setLoadingAgents(true);
    try {
      const res = await axios.get(`${API}/api/watchtower/agents`, { headers });
      setAgents(res.data);
    } catch (error) {
      toast.error('Failed to load agents from WatchTower');
    } finally {
      setLoadingAgents(false);
    }
  };

  const handleSetup = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/api/watchtower/config`, {
        api_url: setupForm.api_url,
        api_key: setupForm.api_key,
        enabled: true
      }, { headers });
      toast.success('WatchTower integration configured successfully');
      setShowSetup(false);
      fetchConfig();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to configure integration');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    if (!selectedCompany) {
      toast.error('Please select a company to sync agents to');
      return;
    }
    
    setSyncing(true);
    try {
      const res = await axios.post(`${API}/api/watchtower/auto-sync`, {}, { headers });
      
      toast.success(`Synced ${res.data.devices_created} new devices, updated ${res.data.devices_updated} existing`);
      fetchAgents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sync agents');
    } finally {
      setSyncing(false);
    }
  };

  const handleReboot = async (agentId) => {
    if (!window.confirm('Are you sure you want to reboot this device?')) return;
    
    try {
      await axios.post(`${API}/api/watchtower/agents/${agentId}/reboot`, {}, { headers });
      toast.success('Reboot command sent');
    } catch (error) {
      toast.error('Failed to send reboot command');
    }
  };

  const handleDisable = async () => {
    if (!window.confirm('Are you sure you want to disable WatchTower integration?')) return;
    
    try {
      await axios.delete(`${API}/api/watchtower/config`, { headers });
      toast.success('Integration disabled');
      setConfig({ configured: false });
      setAgents([]);
    } catch (error) {
      toast.error('Failed to disable integration');
    }
  };

  const handleDownloadAgent = async (companyId, companyName) => {
    setDownloadingFor(companyId);
    try {
      const res = await axios.post(`${API}/api/watchtower/agent-download/${companyId}`, {
        site_name: 'Default Site',
        platform: 'windows',
        arch: '64'
      }, { headers });
      
      if (res.data.download_url) {
        setAgentDownloadUrl(res.data.download_url);
        window.open(res.data.download_url, '_blank');
        toast.success(`Agent download started for ${companyName}`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate download link');
    } finally {
      setDownloadingFor(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="watchtower-integration">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">WatchTower Integration</h1>
          <p className="text-slate-600">Sync agents and manage devices from your WatchTower instance</p>
        </div>
        {config?.configured && (
          <div className="flex items-center gap-2">
            <Badge variant={config.enabled ? 'default' : 'secondary'} className="bg-emerald-500">
              {config.enabled ? 'Connected' : 'Disabled'}
            </Badge>
            <Button variant="outline" size="sm" onClick={() => setShowSetup(true)}>
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        )}
      </div>

      {/* Setup Card */}
      {(!config?.configured || showSetup) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              {config?.configured ? 'Update Configuration' : 'Setup WatchTower'}
            </CardTitle>
            <CardDescription>
              Connect your WatchTower instance to sync agents as devices
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSetup} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="api_url">API URL</Label>
                <Input
                  id="api_url"
                  placeholder="https://api.yourdomain.com"
                  value={setupForm.api_url}
                  onChange={(e) => setSetupForm({ ...setupForm, api_url: e.target.value })}
                  required
                />
                <p className="text-xs text-slate-500">Your WatchTower API endpoint (usually https://api.yourdomain.com)</p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="api_key">API Key</Label>
                <Input
                  id="api_key"
                  type="password"
                  placeholder="Your Tactical RMM API Key"
                  value={setupForm.api_key}
                  onChange={(e) => setSetupForm({ ...setupForm, api_key: e.target.value })}
                  required
                />
                <p className="text-xs text-slate-500">
                  Generate from Settings → Global Settings → API Keys in your Tactical RMM dashboard
                </p>
              </div>
              
              <div className="flex gap-2">
                <Button type="submit" disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                  {config?.configured ? 'Update' : 'Connect'}
                </Button>
                {config?.configured && (
                  <>
                    <Button type="button" variant="outline" onClick={() => setShowSetup(false)}>
                      Cancel
                    </Button>
                    <Button type="button" variant="destructive" onClick={handleDisable}>
                      Disable Integration
                    </Button>
                  </>
                )}
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Agents Section */}
      {config?.configured && config?.enabled && !showSetup && (
        <>
          {/* Sync Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <RefreshCw className="h-5 w-5" />
                Sync Agents
              </CardTitle>
              <CardDescription>
                Import agents from Tactical RMM as devices in your inventory
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-4">
                <div className="flex-1 max-w-xs">
                  <Label htmlFor="company">Assign to Company</Label>
                  <select
                    id="company"
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                    value={selectedCompany}
                    onChange={(e) => setSelectedCompany(e.target.value)}
                  >
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <Button onClick={handleSync} disabled={syncing || !selectedCompany}>
                  {syncing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                  Sync All Agents
                </Button>
                <Button variant="outline" onClick={fetchAgents} disabled={loadingAgents}>
                  {loadingAgents ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                </Button>
              </div>
              {config.last_sync && (
                <p className="text-xs text-slate-500 mt-2">
                  Last synced: {new Date(config.last_sync).toLocaleString()} • {config.agents_count} agents
                </p>
              )}
            </CardContent>
          </Card>

          {/* Agents List */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Monitor className="h-5 w-5" />
                Agents ({agents.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingAgents ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                </div>
              ) : agents.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Server className="h-12 w-12 mx-auto mb-2 text-slate-300" />
                  <p>No agents found. Make sure your Tactical RMM has agents deployed.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3 px-2 font-medium">Status</th>
                        <th className="text-left py-3 px-2 font-medium">Hostname</th>
                        <th className="text-left py-3 px-2 font-medium">Client / Site</th>
                        <th className="text-left py-3 px-2 font-medium">OS</th>
                        <th className="text-left py-3 px-2 font-medium">Last Seen</th>
                        <th className="text-left py-3 px-2 font-medium">Synced</th>
                        <th className="text-left py-3 px-2 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {agents.map((agent) => (
                        <tr key={agent.agent_id} className="border-b hover:bg-slate-50">
                          <td className="py-3 px-2">
                            {agent.status === 'online' ? (
                              <Badge variant="default" className="bg-emerald-500">
                                <Wifi className="h-3 w-3 mr-1" /> Online
                              </Badge>
                            ) : (
                              <Badge variant="secondary">
                                <WifiOff className="h-3 w-3 mr-1" /> Offline
                              </Badge>
                            )}
                          </td>
                          <td className="py-3 px-2 font-medium">{agent.hostname}</td>
                          <td className="py-3 px-2 text-slate-600">
                            {agent.client_name} / {agent.site_name}
                          </td>
                          <td className="py-3 px-2 text-slate-600 truncate max-w-[200px]">
                            {agent.operating_system}
                          </td>
                          <td className="py-3 px-2 text-slate-600">
                            {agent.last_seen ? new Date(agent.last_seen).toLocaleString() : '-'}
                          </td>
                          <td className="py-3 px-2">
                            {agent.synced ? (
                              <CheckCircle className="h-5 w-5 text-emerald-500" />
                            ) : (
                              <XCircle className="h-5 w-5 text-slate-300" />
                            )}
                          </td>
                          <td className="py-3 px-2">
                            <div className="flex items-center gap-1">
                              {agent.needs_reboot && (
                                <Badge variant="outline" className="text-amber-600 border-amber-300">
                                  <AlertTriangle className="h-3 w-3 mr-1" /> Reboot
                                </Badge>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleReboot(agent.agent_id)}
                                title="Reboot"
                              >
                                <RotateCcw className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Agent Download Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="h-5 w-5" />
                Download Agent for Companies
              </CardTitle>
              <CardDescription>
                Generate WatchTower agent installer for a specific company. The agent will auto-register to the company's client in WatchTower.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {companies.length === 0 ? (
                  <div className="text-center py-6 text-slate-500">
                    <Building2 className="h-10 w-10 mx-auto mb-2 text-slate-300" />
                    <p>No companies found. Create a company first.</p>
                  </div>
                ) : (
                  <div className="grid gap-3 max-h-80 overflow-y-auto">
                    {companies.slice(0, 10).map((company) => (
                      <div 
                        key={company.id} 
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50"
                      >
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-indigo-100 rounded-lg">
                            <Building2 className="h-5 w-5 text-indigo-600" />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">{company.name}</p>
                            <p className="text-xs text-slate-500">
                              {company.watchtower_client_id 
                                ? `WatchTower Client: ${company.watchtower_client_id}` 
                                : 'Not provisioned in WatchTower'}
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadAgent(company.id, company.name)}
                          disabled={downloadingFor === company.id}
                          data-testid={`download-agent-${company.id}`}
                        >
                          {downloadingFor === company.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <>
                              <Download className="h-4 w-4 mr-2" />
                              Download Agent
                            </>
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                {companies.length > 10 && (
                  <p className="text-xs text-slate-500 text-center">
                    Showing first 10 companies. Use company search for more.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default TacticalRMMIntegration;
