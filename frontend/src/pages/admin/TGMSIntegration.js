import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Switch } from '../../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../../components/ui/dialog';
import { toast } from 'sonner';
import { 
  Monitor, Terminal, FolderOpen, Download, Settings, Palette,
  Wifi, WifiOff, RefreshCw, TestTube, Check, X, Server,
  Laptop, Apple, Chrome, Copy, ExternalLink, Shield, Eye
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function TGMSIntegration() {
  const [config, setConfig] = useState(null);
  const [configured, setConfigured] = useState(false);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [devices, setDevices] = useState([]);
  const [devicesLoading, setDevicesLoading] = useState(false);
  const [agents, setAgents] = useState([]);
  
  // Form state
  const [formData, setFormData] = useState({
    server_url: '',
    username: '',
    password: '',
    api_token: '',
    mesh_domain: ''
  });
  
  // Branding state
  const [branding, setBranding] = useState({
    title: 'Remote Management',
    title2: 'IT Support Portal',
    welcome_text: 'Welcome to Remote Support',
    logo_url: '',
    login_background_url: '',
    primary_color: '#0F62FE',
    background_color: '#1a1a2e',
    night_mode: true,
    agent_display_name: 'Support Agent',
    agent_description: 'Remote Support Agent',
    agent_company_name: 'IT Support',
    agent_service_name: 'SupportAgent',
    agent_foreground_color: '#FFFFFF',
    agent_background_color: '#0F62FE'
  });
  
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showBrandingModal, setShowBrandingModal] = useState(false);

  const fetchConfig = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/tgms/config`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfigured(data.configured);
        if (data.config) {
          setConfig(data.config);
          setFormData({
            server_url: data.config.server_url || '',
            username: data.config.username || '',
            password: '',
            api_token: '',
            mesh_domain: data.config.mesh_domain || ''
          });
          setBranding(data.config.branding || branding);
        }
      } else if (response.status === 403) {
        toast.error('TGMS integration is not enabled for your organization');
      }
    } catch (error) {
      console.error('Failed to fetch config:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDevices = useCallback(async () => {
    if (!configured || !config?.is_enabled) return;
    
    setDevicesLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/tgms/devices`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDevices(data.devices || []);
      }
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    } finally {
      setDevicesLoading(false);
    }
  }, [configured, config]);

  const fetchAgents = useCallback(async () => {
    if (!configured) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/tgms/agents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAgents(data.agents || []);
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
  }, [configured]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  useEffect(() => {
    if (configured && config?.is_enabled) {
      fetchDevices();
      fetchAgents();
    }
  }, [configured, config, fetchDevices, fetchAgents]);

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      const method = configured ? 'PUT' : 'POST';
      
      const response = await fetch(`${API_URL}/api/admin/tgms/config`, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        toast.success(configured ? 'Configuration updated' : 'Configuration created');
        setShowConfigModal(false);
        fetchConfig();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to save configuration');
      }
    } catch (error) {
      console.error('Failed to save config:', error);
      toast.error('Failed to save configuration');
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/tgms/test-connection`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (data.success) {
        toast.success('Connection successful!');
      } else {
        toast.error(data.message || 'Connection failed');
      }
    } catch (error) {
      toast.error('Connection test failed');
    } finally {
      setTesting(false);
    }
  };

  const handleToggleEnabled = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/tgms/config`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_enabled: !config?.is_enabled })
      });
      
      if (response.ok) {
        toast.success(config?.is_enabled ? 'Integration disabled' : 'Integration enabled');
        fetchConfig();
      }
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const handleSaveBranding = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/tgms/branding`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(branding)
      });
      
      if (response.ok) {
        toast.success('Branding saved');
        setShowBrandingModal(false);
        fetchConfig();
      } else {
        toast.error('Failed to save branding');
      }
    } catch (error) {
      toast.error('Failed to save branding');
    }
  };

  const openRemoteSession = async (deviceId, type) => {
    try {
      const token = localStorage.getItem('token');
      const endpoint = type === 'desktop' ? 'remote-desktop' : 
                       type === 'terminal' ? 'remote-terminal' : 'file-transfer';
      
      const response = await fetch(`${API_URL}/api/admin/tgms/devices/${deviceId}/${endpoint}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        window.open(data.url, '_blank');
      } else {
        toast.error('Failed to get remote session URL');
      }
    } catch (error) {
      toast.error('Failed to open remote session');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'windows': return <Monitor className="h-5 w-5" />;
      case 'linux': return <Terminal className="h-5 w-5" />;
      case 'macos': return <Apple className="h-5 w-5" />;
      default: return <Laptop className="h-5 w-5" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="tgms-integration-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Remote Management</h1>
          <p className="text-slate-500">Manage devices remotely with desktop, terminal, and file access</p>
        </div>
        <div className="flex items-center gap-3">
          {configured && (
            <>
              <Button variant="outline" onClick={() => setShowBrandingModal(true)}>
                <Palette className="h-4 w-4 mr-2" />
                Branding
              </Button>
              <Button variant="outline" onClick={() => setShowConfigModal(true)}>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Connection Status */}
      {!configured ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Server className="h-16 w-16 text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Connect to TGMS Server</h3>
            <p className="text-slate-500 text-center mb-4 max-w-md">
              Configure your TGMS server connection to enable remote device management with full white-label branding.
            </p>
            <Button onClick={() => setShowConfigModal(true)} data-testid="setup-tgms-btn">
              <Settings className="h-4 w-4 mr-2" />
              Configure Connection
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Status Card */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-full ${config?.is_enabled ? 'bg-green-100' : 'bg-slate-100'}`}>
                    {config?.is_enabled ? (
                      <Wifi className="h-6 w-6 text-green-600" />
                    ) : (
                      <WifiOff className="h-6 w-6 text-slate-400" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-medium text-slate-900">
                      {config?.is_enabled ? 'Integration Active' : 'Integration Disabled'}
                    </h3>
                    <p className="text-sm text-slate-500">
                      Server: {config?.server_url || 'Not configured'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Button variant="outline" onClick={handleTestConnection} disabled={testing}>
                    <TestTube className={`h-4 w-4 mr-2 ${testing ? 'animate-pulse' : ''}`} />
                    Test Connection
                  </Button>
                  <div className="flex items-center gap-2">
                    <Label htmlFor="enabled-toggle" className="text-sm">Enabled</Label>
                    <Switch
                      id="enabled-toggle"
                      checked={config?.is_enabled || false}
                      onCheckedChange={handleToggleEnabled}
                    />
                  </div>
                </div>
              </div>
              
              {config?.last_sync_at && (
                <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-sm text-slate-500">
                  <span>Last sync: {new Date(config.last_sync_at).toLocaleString()}</span>
                  <span className={config.last_sync_status === 'success' ? 'text-green-600' : 'text-red-500'}>
                    {config.last_sync_status === 'success' ? '✓ Sync successful' : `✗ ${config.last_sync_error}`}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Main Content Tabs */}
          <Tabs defaultValue="devices">
            <TabsList>
              <TabsTrigger value="devices">
                <Laptop className="h-4 w-4 mr-2" />
                Devices ({devices.length})
              </TabsTrigger>
              <TabsTrigger value="agents">
                <Download className="h-4 w-4 mr-2" />
                Agent Downloads
              </TabsTrigger>
              <TabsTrigger value="features">
                <Shield className="h-4 w-4 mr-2" />
                Features
              </TabsTrigger>
            </TabsList>

            {/* Devices Tab */}
            <TabsContent value="devices" className="mt-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Remote Devices</CardTitle>
                    <CardDescription>
                      {devices.filter(d => d.is_online).length} online, {devices.filter(d => !d.is_online).length} offline
                    </CardDescription>
                  </div>
                  <Button variant="outline" onClick={fetchDevices} disabled={devicesLoading}>
                    <RefreshCw className={`h-4 w-4 ${devicesLoading ? 'animate-spin' : ''}`} />
                  </Button>
                </CardHeader>
                <CardContent>
                  {devices.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <Laptop className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>No devices connected yet</p>
                      <p className="text-sm">Download and install the agent on devices to see them here</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {devices.map((device) => (
                        <div 
                          key={device.id}
                          className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-100"
                          data-testid={`device-${device.id}`}
                        >
                          <div className="flex items-center gap-4">
                            <div className={`p-2 rounded-lg ${device.is_online ? 'bg-green-100' : 'bg-slate-200'}`}>
                              <Monitor className={`h-5 w-5 ${device.is_online ? 'text-green-600' : 'text-slate-400'}`} />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <h4 className="font-medium text-slate-900">{device.name}</h4>
                                <Badge variant={device.is_online ? 'default' : 'secondary'} className="text-xs">
                                  {device.is_online ? 'Online' : 'Offline'}
                                </Badge>
                              </div>
                              <p className="text-sm text-slate-500">
                                {device.os || 'Unknown OS'} • {device.host || 'No hostname'}
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              disabled={!device.is_online}
                              onClick={() => openRemoteSession(device.id, 'desktop')}
                              title="Remote Desktop"
                            >
                              <Monitor className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              disabled={!device.is_online}
                              onClick={() => openRemoteSession(device.id, 'terminal')}
                              title="Remote Terminal"
                            >
                              <Terminal className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              disabled={!device.is_online}
                              onClick={() => openRemoteSession(device.id, 'files')}
                              title="File Transfer"
                            >
                              <FolderOpen className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Agent Downloads Tab */}
            <TabsContent value="agents" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Download Agents</CardTitle>
                  <CardDescription>Install the remote management agent on devices you want to manage</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {agents.map((agent, idx) => (
                      <div 
                        key={idx}
                        className="p-4 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors"
                      >
                        <div className="flex items-center gap-3 mb-3">
                          {getPlatformIcon(agent.platform)}
                          <div>
                            <h4 className="font-medium capitalize">{agent.platform}</h4>
                            <span className="text-xs text-slate-500">{agent.architecture}</span>
                          </div>
                        </div>
                        <p className="text-sm text-slate-600 mb-3 font-mono bg-slate-50 p-2 rounded text-xs">
                          {agent.instructions}
                        </p>
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            className="flex-1"
                            onClick={() => window.open(agent.download_url, '_blank')}
                          >
                            <Download className="h-4 w-4 mr-1" />
                            Download
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => copyToClipboard(agent.download_url)}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Features Tab */}
            <TabsContent value="features" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Feature Settings</CardTitle>
                  <CardDescription>Control which remote management features are available</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Monitor className="h-5 w-5 text-slate-600" />
                      <div>
                        <h4 className="font-medium">Remote Desktop</h4>
                        <p className="text-sm text-slate-500">View and control device screens</p>
                      </div>
                    </div>
                    <Badge variant={config?.allow_remote_desktop ? 'default' : 'secondary'}>
                      {config?.allow_remote_desktop ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Terminal className="h-5 w-5 text-slate-600" />
                      <div>
                        <h4 className="font-medium">Remote Terminal</h4>
                        <p className="text-sm text-slate-500">Command line access to devices</p>
                      </div>
                    </div>
                    <Badge variant={config?.allow_remote_terminal ? 'default' : 'secondary'}>
                      {config?.allow_remote_terminal ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <FolderOpen className="h-5 w-5 text-slate-600" />
                      <div>
                        <h4 className="font-medium">File Transfer</h4>
                        <p className="text-sm text-slate-500">Upload and download files</p>
                      </div>
                    </div>
                    <Badge variant={config?.allow_file_transfer ? 'default' : 'secondary'}>
                      {config?.allow_file_transfer ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      )}

      {/* Configuration Modal */}
      <Dialog open={showConfigModal} onOpenChange={setShowConfigModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>TGMS Configuration</DialogTitle>
            <DialogDescription>Connect to your TGMS server</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSaveConfig} className="space-y-4">
            <div>
              <Label htmlFor="server_url">Server URL *</Label>
              <Input
                id="server_url"
                value={formData.server_url}
                onChange={(e) => setFormData({...formData, server_url: e.target.value})}
                placeholder="https://rmm.yourcompany.com"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="mesh_domain">Domain/Group Name</Label>
              <Input
                id="mesh_domain"
                value={formData.mesh_domain}
                onChange={(e) => setFormData({...formData, mesh_domain: e.target.value})}
                placeholder="mycompany"
              />
              <p className="text-xs text-slate-500 mt-1">Used for agent downloads and branding</p>
            </div>
            
            <div className="border-t pt-4">
              <p className="text-sm font-medium mb-3">Authentication (choose one)</p>
              
              <div className="space-y-3">
                <div>
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                    placeholder="admin"
                  />
                </div>
                
                <div>
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    placeholder="••••••••"
                  />
                </div>
                
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-white px-2 text-slate-500">Or</span>
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="api_token">API Token</Label>
                  <Input
                    id="api_token"
                    value={formData.api_token}
                    onChange={(e) => setFormData({...formData, api_token: e.target.value})}
                    placeholder="Login token from TGMS"
                  />
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowConfigModal(false)}>
                Cancel
              </Button>
              <Button type="submit">
                {configured ? 'Update' : 'Connect'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Branding Modal */}
      <Dialog open={showBrandingModal} onOpenChange={setShowBrandingModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>White-Label Branding</DialogTitle>
            <DialogDescription>Customize the look and feel of your remote management portal</DialogDescription>
          </DialogHeader>
          
          <Tabs defaultValue="portal">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="portal">Portal Branding</TabsTrigger>
              <TabsTrigger value="agent">Agent Branding</TabsTrigger>
            </TabsList>
            
            <TabsContent value="portal" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="brand_title">Portal Title</Label>
                  <Input
                    id="brand_title"
                    value={branding.title}
                    onChange={(e) => setBranding({...branding, title: e.target.value})}
                    placeholder="Remote Management"
                  />
                </div>
                <div>
                  <Label htmlFor="brand_title2">Subtitle</Label>
                  <Input
                    id="brand_title2"
                    value={branding.title2}
                    onChange={(e) => setBranding({...branding, title2: e.target.value})}
                    placeholder="IT Support Portal"
                  />
                </div>
              </div>
              
              <div>
                <Label htmlFor="welcome_text">Welcome Message</Label>
                <Input
                  id="welcome_text"
                  value={branding.welcome_text}
                  onChange={(e) => setBranding({...branding, welcome_text: e.target.value})}
                  placeholder="Welcome to Remote Support"
                />
              </div>
              
              <div>
                <Label htmlFor="logo_url">Logo URL</Label>
                <Input
                  id="logo_url"
                  value={branding.logo_url}
                  onChange={(e) => setBranding({...branding, logo_url: e.target.value})}
                  placeholder="https://yourcompany.com/logo.png"
                />
              </div>
              
              <div>
                <Label htmlFor="login_bg_url">Login Background URL</Label>
                <Input
                  id="login_bg_url"
                  value={branding.login_background_url}
                  onChange={(e) => setBranding({...branding, login_background_url: e.target.value})}
                  placeholder="https://yourcompany.com/background.jpg"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="primary_color">Primary Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="primary_color"
                      value={branding.primary_color}
                      onChange={(e) => setBranding({...branding, primary_color: e.target.value})}
                      placeholder="#0F62FE"
                    />
                    <input 
                      type="color" 
                      value={branding.primary_color}
                      onChange={(e) => setBranding({...branding, primary_color: e.target.value})}
                      className="w-10 h-10 rounded cursor-pointer"
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="bg_color">Background Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="bg_color"
                      value={branding.background_color}
                      onChange={(e) => setBranding({...branding, background_color: e.target.value})}
                      placeholder="#1a1a2e"
                    />
                    <input 
                      type="color" 
                      value={branding.background_color}
                      onChange={(e) => setBranding({...branding, background_color: e.target.value})}
                      className="w-10 h-10 rounded cursor-pointer"
                    />
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <Switch
                  id="night_mode"
                  checked={branding.night_mode}
                  onCheckedChange={(v) => setBranding({...branding, night_mode: v})}
                />
                <Label htmlFor="night_mode">Enable Dark/Night Mode</Label>
              </div>
            </TabsContent>
            
            <TabsContent value="agent" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="agent_display_name">Agent Display Name</Label>
                  <Input
                    id="agent_display_name"
                    value={branding.agent_display_name}
                    onChange={(e) => setBranding({...branding, agent_display_name: e.target.value})}
                    placeholder="Support Agent"
                  />
                </div>
                <div>
                  <Label htmlFor="agent_service_name">Service Name</Label>
                  <Input
                    id="agent_service_name"
                    value={branding.agent_service_name}
                    onChange={(e) => setBranding({...branding, agent_service_name: e.target.value})}
                    placeholder="SupportAgent"
                  />
                  <p className="text-xs text-slate-500 mt-1">No spaces, used for Windows service</p>
                </div>
              </div>
              
              <div>
                <Label htmlFor="agent_description">Agent Description</Label>
                <Input
                  id="agent_description"
                  value={branding.agent_description}
                  onChange={(e) => setBranding({...branding, agent_description: e.target.value})}
                  placeholder="Remote Support Agent"
                />
              </div>
              
              <div>
                <Label htmlFor="agent_company_name">Company Name</Label>
                <Input
                  id="agent_company_name"
                  value={branding.agent_company_name}
                  onChange={(e) => setBranding({...branding, agent_company_name: e.target.value})}
                  placeholder="Your Company Name"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="agent_fg_color">Agent Foreground Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="agent_fg_color"
                      value={branding.agent_foreground_color}
                      onChange={(e) => setBranding({...branding, agent_foreground_color: e.target.value})}
                      placeholder="#FFFFFF"
                    />
                    <input 
                      type="color" 
                      value={branding.agent_foreground_color}
                      onChange={(e) => setBranding({...branding, agent_foreground_color: e.target.value})}
                      className="w-10 h-10 rounded cursor-pointer"
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="agent_bg_color">Agent Background Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="agent_bg_color"
                      value={branding.agent_background_color}
                      onChange={(e) => setBranding({...branding, agent_background_color: e.target.value})}
                      placeholder="#0F62FE"
                    />
                    <input 
                      type="color" 
                      value={branding.agent_background_color}
                      onChange={(e) => setBranding({...branding, agent_background_color: e.target.value})}
                      className="w-10 h-10 rounded cursor-pointer"
                    />
                  </div>
                </div>
              </div>
              
              {/* Preview */}
              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50">
                <Label className="text-xs text-slate-500 mb-2 block">Agent Tray Icon Preview</Label>
                <div 
                  className="inline-flex items-center gap-2 px-3 py-2 rounded"
                  style={{ 
                    backgroundColor: branding.agent_background_color,
                    color: branding.agent_foreground_color
                  }}
                >
                  <Monitor className="h-4 w-4" />
                  <span className="text-sm font-medium">{branding.agent_display_name}</span>
                </div>
              </div>
            </TabsContent>
          </Tabs>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBrandingModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveBranding}>
              Save Branding
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
