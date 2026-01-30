import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, 
  DialogHeader, DialogTitle 
} from '../../components/ui/dialog';
import { Alert, AlertDescription, AlertTitle } from '../../components/ui/alert';
import { toast } from 'sonner';
import { 
  Globe, Plus, Trash2, RefreshCw, CheckCircle, Clock, 
  AlertTriangle, Copy, ExternalLink, Shield, Info
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function CustomDomains() {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newDomain, setNewDomain] = useState('');
  const [saving, setSaving] = useState(false);
  const [verifying, setVerifying] = useState(null);
  const [verificationInstructions, setVerificationInstructions] = useState(null);

  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchDomains();
  }, []);

  const fetchDomains = async () => {
    try {
      const response = await axios.get(`${API}/api/org/custom-domains`, { headers });
      setDomains(response.data || []);
    } catch (error) {
      console.error('Failed to fetch domains:', error);
      toast.error('Failed to load custom domains');
    } finally {
      setLoading(false);
    }
  };

  const handleAddDomain = async () => {
    if (!newDomain.trim()) {
      toast.error('Please enter a domain');
      return;
    }

    setSaving(true);
    try {
      const response = await axios.post(`${API}/api/org/custom-domains`, 
        { domain: newDomain.toLowerCase().trim() },
        { headers }
      );
      
      setVerificationInstructions(response.data);
      setNewDomain('');
      fetchDomains();
      toast.success('Domain added! Please complete DNS verification.');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add domain');
    } finally {
      setSaving(false);
    }
  };

  const handleVerifyDomain = async (domain) => {
    setVerifying(domain);
    try {
      const response = await axios.post(`${API}/api/org/custom-domains/verify`,
        { domain },
        { headers }
      );
      
      if (response.data.verified) {
        toast.success('Domain verified successfully!');
        fetchDomains();
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Verification failed');
    } finally {
      setVerifying(null);
    }
  };

  const handleDeleteDomain = async (domainId, domainName) => {
    if (!confirm(`Are you sure you want to remove ${domainName}?`)) return;
    
    try {
      await axios.delete(`${API}/api/org/custom-domains/${domainId}`, { headers });
      toast.success('Domain removed');
      fetchDomains();
    } catch (error) {
      toast.error('Failed to remove domain');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const getStatusBadge = (domain) => {
    if (domain.verification_status === 'verified') {
      return (
        <Badge className="bg-green-100 text-green-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Verified
        </Badge>
      );
    }
    return (
      <Badge className="bg-amber-100 text-amber-800">
        <Clock className="w-3 h-3 mr-1" />
        Pending Verification
      </Badge>
    );
  };

  const getSSLBadge = (domain) => {
    if (domain.verification_status !== 'verified') return null;
    
    if (domain.ssl_status === 'active') {
      return (
        <Badge className="bg-green-100 text-green-800">
          <Shield className="w-3 h-3 mr-1" />
          SSL Active
        </Badge>
      );
    }
    return (
      <Badge className="bg-blue-100 text-blue-800">
        <Clock className="w-3 h-3 mr-1" />
        SSL Pending
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="custom-domains-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Custom Domains</h1>
          <p className="text-slate-500 mt-1">
            Connect your own domain to access your workspace
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)} data-testid="add-domain-btn">
          <Plus className="w-4 h-4 mr-2" />
          Add Domain
        </Button>
      </div>

      {/* Info Alert */}
      <Alert>
        <Info className="w-4 h-4" />
        <AlertTitle>How Custom Domains Work</AlertTitle>
        <AlertDescription>
          Custom domains allow your team to access the portal via your own domain (e.g., <code>assets.yourcompany.com</code>). 
          You'll need to verify domain ownership by adding a DNS TXT record, then point your domain to our servers.
        </AlertDescription>
      </Alert>

      {/* Verification Instructions Modal */}
      {verificationInstructions && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-blue-900">
                DNS Verification Required
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setVerificationInstructions(null)}
              >
                Dismiss
              </Button>
            </div>
            <CardDescription className="text-blue-700">
              Add the following DNS TXT record to verify ownership of <strong>{verificationInstructions.domain}</strong>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-white rounded-lg p-4 border border-blue-200">
              <div className="grid gap-3">
                <div>
                  <Label className="text-xs text-slate-500">Record Type</Label>
                  <p className="font-mono text-sm font-medium">TXT</p>
                </div>
                <div>
                  <Label className="text-xs text-slate-500">Host / Name</Label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 bg-slate-100 px-2 py-1 rounded text-sm">
                      _aftersales-verification.{verificationInstructions.domain}
                    </code>
                    <Button 
                      variant="ghost" 
                      size="icon"
                      onClick={() => copyToClipboard(`_aftersales-verification.${verificationInstructions.domain}`)}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-slate-500">Value</Label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 bg-slate-100 px-2 py-1 rounded text-sm">
                      {verificationInstructions.verification_token}
                    </code>
                    <Button 
                      variant="ghost" 
                      size="icon"
                      onClick={() => copyToClipboard(verificationInstructions.verification_token)}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
            <p className="text-sm text-blue-700">
              <AlertTriangle className="w-4 h-4 inline mr-1" />
              DNS changes can take up to 48 hours to propagate. After adding the record, click "Verify" on your domain.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Domains List */}
      {domains.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Globe className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900">No custom domains</h3>
            <p className="text-slate-500 mt-1 mb-4">
              Add a custom domain to personalize your workspace URL
            </p>
            <Button onClick={() => setShowAddModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Your First Domain
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {domains.map((domain) => (
            <Card key={domain.id}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                      <Globe className="w-5 h-5 text-slate-600" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-slate-900">{domain.domain}</h3>
                        {domain.is_primary && (
                          <Badge variant="secondary">Primary</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {getStatusBadge(domain)}
                        {getSSLBadge(domain)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {domain.verification_status === 'pending' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleVerifyDomain(domain.domain)}
                        disabled={verifying === domain.domain}
                      >
                        {verifying === domain.domain ? (
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <CheckCircle className="w-4 h-4 mr-2" />
                        )}
                        Verify
                      </Button>
                    )}
                    {domain.verification_status === 'verified' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => window.open(`https://${domain.domain}`, '_blank')}
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Visit
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDeleteDomain(domain.id, domain.domain)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                {/* Verification instructions for pending domains */}
                {domain.verification_status === 'pending' && (
                  <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
                    <p className="text-sm text-amber-800">
                      <AlertTriangle className="w-4 h-4 inline mr-1" />
                      Add a TXT record to <code>_aftersales-verification.{domain.domain}</code> with value: 
                      <code className="ml-1 bg-amber-100 px-1 rounded">{domain.verification_token}</code>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="ml-2 h-6 px-2"
                        onClick={() => copyToClipboard(domain.verification_token)}
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </p>
                  </div>
                )}
                
                {/* CNAME instructions for verified domains without SSL */}
                {domain.verification_status === 'verified' && domain.ssl_status !== 'active' && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-blue-800">
                      <Info className="w-4 h-4 inline mr-1" />
                      Point your domain to <code>app.aftersales.support</code> using a CNAME record.
                      Contact support for SSL certificate provisioning.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add Domain Modal */}
      <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Custom Domain</DialogTitle>
            <DialogDescription>
              Enter the domain you want to use for your workspace
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="domain">Domain</Label>
              <Input
                id="domain"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                placeholder="assets.yourcompany.com"
              />
              <p className="text-xs text-slate-500">
                Enter a subdomain or root domain. You must have access to its DNS settings.
              </p>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddDomain} disabled={saving}>
              {saving ? 'Adding...' : 'Add Domain'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
