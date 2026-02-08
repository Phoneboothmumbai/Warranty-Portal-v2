import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Download, Monitor, Wifi, WifiOff, RefreshCw, 
  ChevronDown, CheckCircle2, AlertCircle, Laptop,
  Server, HelpCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * WatchTower Agent Download Component
 * Used in Company Portal for self-service agent download
 */
const WatchTowerAgentDownload = ({ token, variant = 'button', onSuccess }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [sites, setSites] = useState([]);
  const [selectedSite, setSelectedSite] = useState('');
  const [platform, setPlatform] = useState('windows');
  const [downloadUrl, setDownloadUrl] = useState(null);
  
  const headers = { Authorization: `Bearer ${token}` };
  
  // Fetch WatchTower status on mount
  useEffect(() => {
    fetchStatus();
    fetchSites();
  }, []);
  
  const fetchStatus = async () => {
    try {
      setStatusLoading(true);
      const response = await axios.get(`${API}/watchtower/company/agent-status`, { headers });
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch WatchTower status:', error);
      setStatus({ watchtower_enabled: false });
    } finally {
      setStatusLoading(false);
    }
  };
  
  const fetchSites = async () => {
    try {
      const response = await axios.get(`${API}/watchtower/company/sites-for-agent`, { headers });
      setSites(response.data.sites || []);
    } catch (error) {
      console.error('Failed to fetch sites:', error);
    }
  };
  
  const [downloadInstructions, setDownloadInstructions] = useState(null);
  
  const handleDownload = async () => {
    try {
      setLoading(true);
      const response = await axios.post(
        `${API}/watchtower/company/agent-download`,
        {
          site_id: selectedSite || null,
          platform: platform,
          arch: '64'
        },
        { headers }
      );
      
      if (response.data.manual_download_required) {
        // Show instructions instead of redirecting
        setDownloadInstructions(response.data);
        setDownloadUrl(response.data.install_page_url || response.data.web_ui_url);
        toast.info('Please follow the instructions to download the agent.', { duration: 4000 });
        if (onSuccess) onSuccess(response.data);
      } else if (response.data.download_url) {
        setDownloadUrl(response.data.download_url);
        window.open(response.data.download_url, '_blank');
        toast.success('Agent download started!');
        if (onSuccess) onSuccess(response.data);
      } else {
        toast.error('Failed to generate download link');
      }
    } catch (error) {
      console.error('Download failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate download link');
    } finally {
      setLoading(false);
    }
  };
  
  // If WatchTower is not enabled, show disabled state
  if (!statusLoading && !status?.watchtower_enabled) {
    if (variant === 'inline') {
      return (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-center">
          <Monitor className="h-8 w-8 text-slate-400 mx-auto mb-2" />
          <p className="text-slate-600 text-sm">Remote monitoring not available</p>
        </div>
      );
    }
    return null;
  }
  
  // Button variant - just shows the download button
  if (variant === 'button') {
    return (
      <>
        <Button
          onClick={() => setOpen(true)}
          variant="outline"
          className="gap-2"
          data-testid="watchtower-download-btn"
        >
          <Download className="h-4 w-4" />
          Download WatchTower Agent
        </Button>
        
        <DownloadDialog
          open={open}
          onOpenChange={setOpen}
          status={status}
          sites={sites}
          selectedSite={selectedSite}
          setSelectedSite={setSelectedSite}
          platform={platform}
          setPlatform={setPlatform}
          loading={loading}
          onDownload={handleDownload}
          downloadUrl={downloadUrl}
        />
      </>
    );
  }
  
  // Card variant - shows status and download option
  if (variant === 'card') {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6" data-testid="watchtower-card">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Monitor className="h-6 w-6 text-indigo-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">WatchTower Monitoring</h3>
              <p className="text-sm text-slate-500">Remote device monitoring agent</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchStatus}>
            <RefreshCw className={`h-4 w-4 ${statusLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        
        {statusLoading ? (
          <div className="flex items-center justify-center py-4">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {/* Status Summary */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <div className="text-2xl font-bold text-slate-900">{status?.total_agents || 0}</div>
                <div className="text-xs text-slate-500">Total Agents</div>
              </div>
              <div className="text-center p-3 bg-emerald-50 rounded-lg">
                <div className="text-2xl font-bold text-emerald-600">{status?.online_agents || 0}</div>
                <div className="text-xs text-emerald-600">Online</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{status?.offline_agents || 0}</div>
                <div className="text-xs text-red-600">Offline</div>
              </div>
            </div>
            
            {/* Download Button */}
            <Button
              onClick={() => setOpen(true)}
              className="w-full gap-2 bg-indigo-600 hover:bg-indigo-700"
              data-testid="watchtower-download-btn-card"
            >
              <Download className="h-4 w-4" />
              Download Agent for New Device
            </Button>
          </>
        )}
        
        <DownloadDialog
          open={open}
          onOpenChange={setOpen}
          status={status}
          sites={sites}
          selectedSite={selectedSite}
          setSelectedSite={setSelectedSite}
          platform={platform}
          setPlatform={setPlatform}
          loading={loading}
          onDownload={handleDownload}
          downloadUrl={downloadUrl}
        />
      </div>
    );
  }
  
  // Inline variant - compact status for device dashboard
  if (variant === 'inline') {
    return (
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Monitor className="h-5 w-5 text-indigo-600" />
            <span className="font-medium text-indigo-900">WatchTower Agent</span>
          </div>
          <Button
            size="sm"
            onClick={() => setOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700"
            data-testid="watchtower-download-inline"
          >
            <Download className="h-4 w-4 mr-1" />
            Download
          </Button>
        </div>
        <p className="text-sm text-indigo-700 mt-2">
          Install the monitoring agent to enable real-time device tracking
        </p>
        
        <DownloadDialog
          open={open}
          onOpenChange={setOpen}
          status={status}
          sites={sites}
          selectedSite={selectedSite}
          setSelectedSite={setSelectedSite}
          platform={platform}
          setPlatform={setPlatform}
          loading={loading}
          onDownload={handleDownload}
          downloadUrl={downloadUrl}
        />
      </div>
    );
  }
  
  return null;
};


/**
 * Download Dialog Component
 */
const DownloadDialog = ({
  open,
  onOpenChange,
  status,
  sites,
  selectedSite,
  setSelectedSite,
  platform,
  setPlatform,
  loading,
  onDownload,
  downloadUrl
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5 text-indigo-600" />
            Download WatchTower Agent
          </DialogTitle>
          <DialogDescription>
            Install the WatchTower agent on your devices to enable real-time monitoring.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 mt-4">
          {/* Platform Selection */}
          <div>
            <label className="text-sm font-medium text-slate-700 mb-2 block">
              Operating System
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setPlatform('windows')}
                className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
                  platform === 'windows' 
                    ? 'border-indigo-600 bg-indigo-50' 
                    : 'border-slate-200 hover:border-slate-300'
                }`}
                data-testid="platform-windows"
              >
                <Laptop className={`h-6 w-6 ${platform === 'windows' ? 'text-indigo-600' : 'text-slate-400'}`} />
                <div className="text-left">
                  <div className={`font-medium ${platform === 'windows' ? 'text-indigo-900' : 'text-slate-700'}`}>
                    Windows
                  </div>
                  <div className="text-xs text-slate-500">Windows 10/11, Server</div>
                </div>
              </button>
              
              <button
                onClick={() => setPlatform('linux')}
                className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
                  platform === 'linux' 
                    ? 'border-indigo-600 bg-indigo-50' 
                    : 'border-slate-200 hover:border-slate-300'
                }`}
                data-testid="platform-linux"
              >
                <Server className={`h-6 w-6 ${platform === 'linux' ? 'text-indigo-600' : 'text-slate-400'}`} />
                <div className="text-left">
                  <div className={`font-medium ${platform === 'linux' ? 'text-indigo-900' : 'text-slate-700'}`}>
                    Linux
                  </div>
                  <div className="text-xs text-slate-500">Ubuntu, Debian, CentOS</div>
                </div>
              </button>
            </div>
          </div>
          
          {/* Site Selection (Optional) */}
          {sites.length > 0 && (
            <div>
              <label className="text-sm font-medium text-slate-700 mb-2 block">
                Site/Location (Optional)
              </label>
              <Select value={selectedSite || 'default'} onValueChange={(val) => setSelectedSite(val === 'default' ? '' : val)}>
                <SelectTrigger data-testid="site-select">
                  <SelectValue placeholder="Select a site..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">Default Site</SelectItem>
                  {sites.map(site => (
                    <SelectItem key={site.id} value={site.id}>
                      {site.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500 mt-1">
                Optionally assign this agent to a specific location
              </p>
            </div>
          )}
          
          {/* Installation Instructions */}
          <div className="bg-slate-50 rounded-lg p-4">
            <h4 className="font-medium text-slate-900 mb-2 flex items-center gap-2">
              <HelpCircle className="h-4 w-4 text-slate-500" />
              Installation Instructions
            </h4>
            {platform === 'windows' ? (
              <ol className="text-sm text-slate-600 space-y-1 list-decimal list-inside">
                <li>Download the .exe installer file</li>
                <li>Right-click and select "Run as Administrator"</li>
                <li>Follow the installation prompts</li>
                <li>Agent will auto-connect after install</li>
              </ol>
            ) : (
              <ol className="text-sm text-slate-600 space-y-1 list-decimal list-inside">
                <li>Download the installer script</li>
                <li>Open terminal: <code className="bg-slate-200 px-1 rounded">chmod +x installer.sh</code></li>
                <li>Run: <code className="bg-slate-200 px-1 rounded">sudo ./installer.sh</code></li>
                <li>Agent will auto-connect after install</li>
              </ol>
            )}
          </div>
          
          {/* Download Button */}
          <Button
            onClick={onDownload}
            disabled={loading}
            className="w-full gap-2 bg-indigo-600 hover:bg-indigo-700"
            data-testid="download-agent-btn"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Getting Download Instructions...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Get {platform === 'windows' ? 'Windows' : 'Linux'} Agent
              </>
            )}
          </Button>
          
          {/* Download Instructions */}
          {downloadUrl && (
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 space-y-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-indigo-900">Manual Download Required</p>
                  <p className="text-xs text-indigo-700 mt-1">
                    WatchTower requires admin access to download agents. Follow these steps:
                  </p>
                </div>
              </div>
              
              <ol className="text-sm text-indigo-800 space-y-2 ml-7 list-decimal">
                <li>
                  <a 
                    href={downloadUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-indigo-600 underline hover:text-indigo-800 font-medium"
                  >
                    Open WatchTower →
                  </a>
                </li>
                <li>Log in with your admin credentials</li>
                <li>Go to <strong>Agents → Install Agent</strong></li>
                <li>Select the correct <strong>Client</strong> and <strong>Site</strong></li>
                <li>Choose <strong>{platform === 'windows' ? 'Windows 64-bit' : 'Linux'}</strong></li>
                <li>Click <strong>Download</strong></li>
              </ol>
              
              <p className="text-xs text-indigo-600 ml-7">
                Contact your administrator if you don't have WatchTower login credentials.
              </p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default WatchTowerAgentDownload;
