import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Upload, Save, Palette, Building2, ImageIcon, X } from 'lucide-react';
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
    logo_base64: ''
  });
  const [logoPreview, setLogoPreview] = useState(null);

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
        logo_base64: response.data.logo_base64 || ''
      });
      setLogoPreview(response.data.logo_base64 || response.data.logo_url || null);
    } catch (error) {
      toast.error('Failed to fetch settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings.company_name.trim()) {
      toast.error('Company name is required');
      return;
    }

    setSaving(true);
    try {
      await axios.put(`${API}/admin/settings`, {
        company_name: settings.company_name,
        accent_color: settings.accent_color
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Settings saved');
      refreshSettings();
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
        <p className="text-slate-500 mt-1">Configure your portal branding</p>
      </div>

      {/* Branding Section */}
      <div className="card-elevated space-y-6">
        <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Building2 className="h-5 w-5 text-slate-400" />
          Portal Branding
        </h2>

        {/* Company Name */}
        <div>
          <label className="form-label">Portal Name</label>
          <input
            type="text"
            value={settings.company_name}
            onChange={(e) => setSettings({ ...settings, company_name: e.target.value })}
            className="form-input max-w-md"
            placeholder="e.g., NeoStore Warranty Portal"
            data-testid="settings-company-name-input"
          />
          <p className="text-xs text-slate-500 mt-1">This name appears in the header and PDF reports</p>
        </div>

        {/* Logo Upload */}
        <div>
          <label className="form-label flex items-center gap-2">
            <ImageIcon className="h-4 w-4" />
            Logo
          </label>
          <div className="flex items-start gap-6">
            {/* Logo Preview */}
            <div className="w-32 h-32 bg-slate-100 rounded-xl flex items-center justify-center border-2 border-dashed border-slate-200 relative overflow-hidden">
              {logoPreview ? (
                <>
                  <img 
                    src={logoPreview} 
                    alt="Logo preview" 
                    className="max-w-full max-h-full object-contain p-2"
                  />
                  <button
                    onClick={removeLogo}
                    className="absolute top-1 right-1 w-6 h-6 bg-white rounded-full shadow flex items-center justify-center hover:bg-red-50"
                    data-testid="remove-logo-btn"
                  >
                    <X className="h-3 w-3 text-red-500" />
                  </button>
                </>
              ) : (
                <ImageIcon className="h-8 w-8 text-slate-300" />
              )}
            </div>

            {/* Upload Button */}
            <div>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleLogoUpload}
                accept="image/*"
                className="hidden"
              />
              <Button 
                variant="outline" 
                onClick={() => fileInputRef.current?.click()}
                data-testid="upload-logo-btn"
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Logo
              </Button>
              <p className="text-xs text-slate-500 mt-2">
                Recommended: Square image, PNG or SVG<br />
                Max size: 2MB
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Accent Color Section */}
      <div className="card-elevated space-y-6">
        <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Palette className="h-5 w-5 text-slate-400" />
          Accent Color
        </h2>

        <div>
          <label className="form-label">Primary Color</label>
          <div className="flex flex-wrap gap-3 mb-4">
            {predefinedColors.map((color) => (
              <button
                key={color.value}
                onClick={() => setSettings({ ...settings, accent_color: color.value })}
                className={`w-10 h-10 rounded-lg border-2 transition-all ${
                  settings.accent_color === color.value 
                    ? 'border-slate-900 scale-110' 
                    : 'border-transparent hover:scale-105'
                }`}
                style={{ backgroundColor: color.value }}
                title={color.name}
                data-testid={`color-${color.name.toLowerCase().replace(' ', '-')}`}
              />
            ))}
          </div>
          
          {/* Custom Color */}
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-lg border border-slate-200"
              style={{ backgroundColor: settings.accent_color }}
            />
            <input
              type="text"
              value={settings.accent_color}
              onChange={(e) => setSettings({ ...settings, accent_color: e.target.value })}
              className="form-input w-32 font-mono text-sm"
              placeholder="#0F62FE"
              data-testid="custom-color-input"
            />
            <span className="text-sm text-slate-500">Custom hex color</span>
          </div>
        </div>

        {/* Preview */}
        <div className="p-4 bg-slate-50 rounded-xl">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Preview</p>
          <div className="flex items-center gap-4">
            <Button 
              className="text-white"
              style={{ backgroundColor: settings.accent_color }}
            >
              Primary Button
            </Button>
            <span 
              className="px-3 py-1 rounded-full text-sm font-medium"
              style={{ 
                backgroundColor: `${settings.accent_color}15`,
                color: settings.accent_color
              }}
            >
              Badge
            </span>
            <span style={{ color: settings.accent_color }} className="text-sm font-medium">
              Link Text
            </span>
          </div>
        </div>
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
