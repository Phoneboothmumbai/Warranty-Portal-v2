import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { Badge } from '../../components/ui/badge';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Separator } from '../../components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '../../components/ui/alert';
import { toast } from 'sonner';
import { 
  Mail, Save, TestTube, CheckCircle, AlertTriangle, 
  Info, Eye, EyeOff, RefreshCw, Shield, Sparkles
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// SMTP Provider presets
const SMTP_PRESETS = {
  custom: { name: 'Custom SMTP', host: '', port: 587 },
  sendgrid: { name: 'SendGrid', host: 'smtp.sendgrid.net', port: 587 },
  mailgun: { name: 'Mailgun', host: 'smtp.mailgun.org', port: 587 },
  ses: { name: 'Amazon SES', host: 'email-smtp.us-east-1.amazonaws.com', port: 587 },
  postmark: { name: 'Postmark', host: 'smtp.postmarkapp.com', port: 587 },
  smtp2go: { name: 'SMTP2GO', host: 'mail.smtp2go.com', port: 2525 },
  gmail: { name: 'Gmail', host: 'smtp.gmail.com', port: 587 },
  outlook: { name: 'Outlook/O365', host: 'smtp.office365.com', port: 587 }
};

export default function EmailWhitelabel() {
  const [settings, setSettings] = useState({
    email_enabled: false,
    from_email: '',
    from_name: '',
    reply_to: '',
    smtp_provider: 'custom',
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_use_tls: true,
    // Branding
    show_powered_by: true,
    email_logo_url: '',
    email_footer_text: '',
    email_primary_color: '#0F62FE'
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [activeTab, setActiveTab] = useState('smtp');

  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/api/org/email-settings`, { headers });
      if (response.data) {
        setSettings(prev => ({ ...prev, ...response.data }));
      }
    } catch (error) {
      console.error('Failed to fetch email settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = (provider) => {
    const preset = SMTP_PRESETS[provider];
    setSettings(prev => ({
      ...prev,
      smtp_provider: provider,
      smtp_host: preset.host,
      smtp_port: preset.port
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/api/org/email-settings`, settings, { headers });
      toast.success('Email settings saved successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    if (!testEmail) {
      toast.error('Please enter a test email address');
      return;
    }

    setTesting(true);
    try {
      await axios.post(`${API}/api/org/email-settings/test`, 
        { email: testEmail },
        { headers }
      );
      toast.success('Test email sent! Check your inbox.');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send test email');
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="email-whitelabel-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Email White-labeling</h1>
          <p className="text-slate-500 mt-1">
            Configure custom email sending with your own domain
          </p>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save Settings
        </Button>
      </div>

      {/* Enable/Disable Toggle */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Mail className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-medium text-slate-900">Custom Email Sending</h3>
                <p className="text-sm text-slate-500">
                  Send emails from your own domain instead of the default
                </p>
              </div>
            </div>
            <Switch
              checked={settings.email_enabled}
              onCheckedChange={(checked) => setSettings(prev => ({ ...prev, email_enabled: checked }))}
            />
          </div>
        </CardContent>
      </Card>

      {settings.email_enabled && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="smtp">
              <Shield className="w-4 h-4 mr-2" />
              SMTP Settings
            </TabsTrigger>
            <TabsTrigger value="sender">
              <Mail className="w-4 h-4 mr-2" />
              Sender Info
            </TabsTrigger>
            <TabsTrigger value="branding">
              <Sparkles className="w-4 h-4 mr-2" />
              Branding
            </TabsTrigger>
          </TabsList>

          {/* SMTP Settings */}
          <TabsContent value="smtp">
            <Card>
              <CardHeader>
                <CardTitle>SMTP Configuration</CardTitle>
                <CardDescription>
                  Configure your SMTP server for sending emails
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Provider Selection */}
                <div className="space-y-2">
                  <Label>Email Provider</Label>
                  <Select 
                    value={settings.smtp_provider} 
                    onValueChange={handleProviderChange}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select provider" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(SMTP_PRESETS).map(([key, preset]) => (
                        <SelectItem key={key} value={key}>
                          {preset.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Separator />

                {/* SMTP Details */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="smtp-host">SMTP Host</Label>
                    <Input
                      id="smtp-host"
                      value={settings.smtp_host}
                      onChange={(e) => setSettings(prev => ({ ...prev, smtp_host: e.target.value }))}
                      placeholder="smtp.example.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp-port">Port</Label>
                    <Input
                      id="smtp-port"
                      type="number"
                      value={settings.smtp_port}
                      onChange={(e) => setSettings(prev => ({ ...prev, smtp_port: parseInt(e.target.value) }))}
                      placeholder="587"
                    />
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="smtp-username">Username / API Key</Label>
                    <Input
                      id="smtp-username"
                      value={settings.smtp_username}
                      onChange={(e) => setSettings(prev => ({ ...prev, smtp_username: e.target.value }))}
                      placeholder="apikey or username"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp-password">Password / Secret</Label>
                    <div className="relative">
                      <Input
                        id="smtp-password"
                        type={showPassword ? 'text' : 'password'}
                        value={settings.smtp_password}
                        onChange={(e) => setSettings(prev => ({ ...prev, smtp_password: e.target.value }))}
                        placeholder="••••••••"
                        className="pr-10"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Switch
                    checked={settings.smtp_use_tls}
                    onCheckedChange={(checked) => setSettings(prev => ({ ...prev, smtp_use_tls: checked }))}
                  />
                  <Label>Use TLS/SSL encryption</Label>
                </div>

                {/* Test Connection */}
                <Alert>
                  <TestTube className="w-4 h-4" />
                  <AlertTitle>Test Your Configuration</AlertTitle>
                  <AlertDescription className="mt-2">
                    <div className="flex gap-2">
                      <Input
                        value={testEmail}
                        onChange={(e) => setTestEmail(e.target.value)}
                        placeholder="your@email.com"
                        className="max-w-xs"
                      />
                      <Button 
                        variant="outline" 
                        onClick={handleTestEmail}
                        disabled={testing}
                      >
                        {testing ? (
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Mail className="w-4 h-4 mr-2" />
                        )}
                        Send Test
                      </Button>
                    </div>
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sender Info */}
          <TabsContent value="sender">
            <Card>
              <CardHeader>
                <CardTitle>Sender Information</CardTitle>
                <CardDescription>
                  Configure how your emails appear to recipients
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="from-email">From Email Address</Label>
                    <Input
                      id="from-email"
                      type="email"
                      value={settings.from_email}
                      onChange={(e) => setSettings(prev => ({ ...prev, from_email: e.target.value }))}
                      placeholder="noreply@yourcompany.com"
                    />
                    <p className="text-xs text-slate-500">
                      Must be verified with your email provider
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="from-name">From Name</Label>
                    <Input
                      id="from-name"
                      value={settings.from_name}
                      onChange={(e) => setSettings(prev => ({ ...prev, from_name: e.target.value }))}
                      placeholder="Your Company Name"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reply-to">Reply-To Address</Label>
                  <Input
                    id="reply-to"
                    type="email"
                    value={settings.reply_to}
                    onChange={(e) => setSettings(prev => ({ ...prev, reply_to: e.target.value }))}
                    placeholder="support@yourcompany.com"
                  />
                  <p className="text-xs text-slate-500">
                    Where replies should be directed (optional)
                  </p>
                </div>

                {/* Preview */}
                <div className="p-4 bg-slate-50 rounded-lg border">
                  <Label className="text-xs text-slate-500 mb-2 block">Preview</Label>
                  <div className="font-mono text-sm">
                    From: {settings.from_name || 'Your Company'} &lt;{settings.from_email || 'noreply@example.com'}&gt;
                  </div>
                  {settings.reply_to && (
                    <div className="font-mono text-sm text-slate-600">
                      Reply-To: {settings.reply_to}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Branding */}
          <TabsContent value="branding">
            <Card>
              <CardHeader>
                <CardTitle>Email Branding</CardTitle>
                <CardDescription>
                  Customize how your emails look
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="email-logo">Logo URL</Label>
                  <Input
                    id="email-logo"
                    value={settings.email_logo_url}
                    onChange={(e) => setSettings(prev => ({ ...prev, email_logo_url: e.target.value }))}
                    placeholder="https://yourcompany.com/logo.png"
                  />
                  <p className="text-xs text-slate-500">
                    Recommended size: 200x50px, PNG or JPG
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="primary-color">Primary Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="primary-color"
                      type="color"
                      value={settings.email_primary_color}
                      onChange={(e) => setSettings(prev => ({ ...prev, email_primary_color: e.target.value }))}
                      className="w-16 h-10 p-1 cursor-pointer"
                    />
                    <Input
                      value={settings.email_primary_color}
                      onChange={(e) => setSettings(prev => ({ ...prev, email_primary_color: e.target.value }))}
                      placeholder="#0F62FE"
                      className="flex-1"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="footer-text">Footer Text</Label>
                  <Input
                    id="footer-text"
                    value={settings.email_footer_text}
                    onChange={(e) => setSettings(prev => ({ ...prev, email_footer_text: e.target.value }))}
                    placeholder="© 2025 Your Company. All rights reserved."
                  />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Show "Powered by" Badge</Label>
                    <p className="text-xs text-slate-500 mt-1">
                      Display "Powered by AfterSales" in email footer
                    </p>
                  </div>
                  <Switch
                    checked={settings.show_powered_by}
                    onCheckedChange={(checked) => setSettings(prev => ({ ...prev, show_powered_by: checked }))}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
