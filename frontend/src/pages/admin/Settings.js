import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Upload, Save, Palette, Building2, ImageIcon, X, Mail } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useSettings } from '../../context/SettingsContext';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const predefinedColors = [
  { name: 'Trust Blue', value: '#0F62FE' },
  { name: 'Emerald', value: '#059669' },
  { name: 'Slate', value: '#475569' },
  { name: 'Indigo', value: '#4F46E5' },
  { name: 'Amber', value: '#D97706' },
  { name: 'Rose', value: '#E11D48' },
];

const Settings = () => {
  const { token } = useAuth();
  const { refreshSettings } = useSettings();
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    company_name: '',
    accent_color: '#0F62FE',
    logo_url: '',
    logo_base64: '',
    billing_emails: [],
  });
  const [logoPreview, setLogoPreview] = useState(null);
  const [newBillingEmail, setNewBillingEmail] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSettings({
        company_name: response.data.company_name || 'aftersales.support',
        accent_color: response.data.accent_color || '#0F62FE',
        logo_url: response.data.logo_url || '',
        logo_base64: response.data.logo_base64 || '',
        billing_emails: response.data.billing_emails || [],
      });
      setLogoPreview(response.data.logo_base64 || response.data.logo_url || null);
    } catch (error) {
      toast.error('Failed to fetch settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/settings`, {
        billing_emails: settings.billing_emails,
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Settings saved');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error('Image size should be less than 2MB');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/admin/settings/logo`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      setLogoPreview(response.data.logo_base64);
      setSettings({ ...settings, logo_base64: response.data.logo_base64 });
      toast.success('Logo uploaded');
      refreshSettings();
    } catch (error) {
      toast.error('Failed to upload logo');
    }
  };

  const removeLogo = async () => {
    try {
      await axios.put(`${API}/admin/settings`, {
        logo_base64: null,
        logo_url: null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLogoPreview(null);
      setSettings({ ...settings, logo_base64: '', logo_url: '' });
      toast.success('Logo removed');
      refreshSettings();
    } catch (error) {
      toast.error('Failed to remove logo');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl" data-testid="settings-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="text-slate-500 mt-1">Configure your portal settings</p>
      </div>

      {/* Billing Email Section */}
      <div className="card-elevated space-y-6">
        <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Mail className="h-5 w-5 text-slate-400" />
          Billing Team Emails
        </h2>
        <p className="text-sm text-slate-500 -mt-4">These email addresses receive notifications when parts are consumed during field visits</p>

        <div className="flex gap-2">
          <input
            type="email"
            value={newBillingEmail}
            onChange={(e) => setNewBillingEmail(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && newBillingEmail.trim()) {
                e.preventDefault();
                if (!settings.billing_emails.includes(newBillingEmail.trim())) {
                  setSettings({ ...settings, billing_emails: [...settings.billing_emails, newBillingEmail.trim()] });
                }
                setNewBillingEmail('');
              }
            }}
            className="form-input flex-1 max-w-sm"
            placeholder="billing@company.com"
            data-testid="billing-email-input"
          />
          <Button
            variant="outline"
            onClick={() => {
              if (newBillingEmail.trim() && !settings.billing_emails.includes(newBillingEmail.trim())) {
                setSettings({ ...settings, billing_emails: [...settings.billing_emails, newBillingEmail.trim()] });
                setNewBillingEmail('');
              }
            }}
            data-testid="add-billing-email-btn"
          >
            Add
          </Button>
        </div>

        {settings.billing_emails.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {settings.billing_emails.map((email, i) => (
              <span key={i} className="inline-flex items-center gap-1.5 bg-blue-50 text-blue-700 text-sm px-3 py-1.5 rounded-full">
                {email}
                <button
                  onClick={() => setSettings({ ...settings, billing_emails: settings.billing_emails.filter((_, j) => j !== i) })}
                  className="w-4 h-4 rounded-full bg-blue-200 hover:bg-blue-300 flex items-center justify-center"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button 
          onClick={handleSave}
          disabled={saving}
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-8"
          data-testid="save-settings-btn"
        >
          {saving ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Settings
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default Settings;
