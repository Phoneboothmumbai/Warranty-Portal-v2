import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Save, Mail, Phone, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useSettings } from '../../context/SettingsContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PhoneField = ({ label, description, value, onChange, testId }) => (
  <div>
    <label className="text-sm font-medium text-slate-700 block mb-1">{label}</label>
    {description && <p className="text-xs text-slate-400 mb-2">{description}</p>}
    <Input
      type="tel"
      value={value || ''}
      onChange={e => onChange(e.target.value)}
      placeholder="e.g. 919876543210 (with country code)"
      className="max-w-sm"
      data-testid={testId}
    />
  </div>
);

const EmailListField = ({ label, description, emails, onAdd, onRemove, testIdPrefix }) => {
  const [val, setVal] = useState('');
  const add = () => {
    if (val.trim() && !emails.includes(val.trim())) {
      onAdd(val.trim());
      setVal('');
    }
  };
  return (
    <div>
      <label className="text-sm font-medium text-slate-700 block mb-1">{label}</label>
      {description && <p className="text-xs text-slate-400 mb-2">{description}</p>}
      <div className="flex gap-2 mb-2">
        <input
          type="email"
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add(); } }}
          className="form-input flex-1 max-w-sm"
          placeholder="email@company.com"
          data-testid={`${testIdPrefix}-input`}
        />
        <Button variant="outline" onClick={add} data-testid={`${testIdPrefix}-add-btn`}>Add</Button>
      </div>
      {emails.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {emails.map((email, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 bg-blue-50 text-blue-700 text-sm px-3 py-1.5 rounded-full">
              {email}
              <button onClick={() => onRemove(i)} className="w-4 h-4 rounded-full bg-blue-200 hover:bg-blue-300 flex items-center justify-center">
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

const Settings = () => {
  const { token } = useAuth();
  const { refreshSettings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    billing_emails: [],
    billing_team_phone: '',
    parts_order_phone: '',
    parts_order_emails: [],
    quote_team_phone: '',
    quote_team_emails: [],
    backend_team_phone: '',
  });

  useEffect(() => { fetchSettings(); }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const d = response.data;
      setSettings({
        billing_emails: d.billing_emails || [],
        billing_team_phone: d.billing_team_phone || '',
        parts_order_phone: d.parts_order_phone || '',
        parts_order_emails: d.parts_order_emails || [],
        quote_team_phone: d.quote_team_phone || '',
        quote_team_emails: d.quote_team_emails || [],
        backend_team_phone: d.backend_team_phone || '',
      });
    } catch {
      toast.error('Failed to fetch settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/settings`, settings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Settings saved');
      refreshSettings();
    } catch {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const updateField = (field, value) => setSettings(s => ({ ...s, [field]: value }));
  const addToList = (field, val) => setSettings(s => ({ ...s, [field]: [...(s[field] || []), val] }));
  const removeFromList = (field, idx) => setSettings(s => ({ ...s, [field]: s[field].filter((_, i) => i !== idx) }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl" data-testid="settings-page">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="text-slate-500 mt-1">Configure notification recipients for WhatsApp and Email</p>
      </div>

      {/* Billing Team */}
      <div className="bg-white border rounded-lg p-6 space-y-5">
        <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
          <Mail className="h-4 w-4 text-slate-400" />
          Billing Team
        </h2>
        <PhoneField
          label="Billing Team WhatsApp Number"
          description="WhatsApp number for billing notifications (include country code, e.g. 919876543210)"
          value={settings.billing_team_phone}
          onChange={v => updateField('billing_team_phone', v)}
          testId="billing-team-phone"
        />
        <EmailListField
          label="Billing Team Emails"
          description="Email addresses that receive billing notifications"
          emails={settings.billing_emails}
          onAdd={v => addToList('billing_emails', v)}
          onRemove={i => removeFromList('billing_emails', i)}
          testIdPrefix="billing-email"
        />
      </div>

      {/* Parts Order Team */}
      <div className="bg-white border rounded-lg p-6 space-y-5">
        <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
          <Phone className="h-4 w-4 text-slate-400" />
          Parts Order Team
        </h2>
        <PhoneField
          label="Parts Order WhatsApp Number"
          description="WhatsApp number for parts order notifications"
          value={settings.parts_order_phone}
          onChange={v => updateField('parts_order_phone', v)}
          testId="parts-order-phone"
        />
        <EmailListField
          label="Parts Order Team Emails"
          description="Email addresses for parts order notifications"
          emails={settings.parts_order_emails}
          onAdd={v => addToList('parts_order_emails', v)}
          onRemove={i => removeFromList('parts_order_emails', i)}
          testIdPrefix="parts-order-email"
        />
      </div>

      {/* Quotation Team */}
      <div className="bg-white border rounded-lg p-6 space-y-5">
        <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
          <Phone className="h-4 w-4 text-slate-400" />
          Quotation Team
        </h2>
        <PhoneField
          label="Quote Team WhatsApp Number"
          description="WhatsApp number for quotation notifications"
          value={settings.quote_team_phone}
          onChange={v => updateField('quote_team_phone', v)}
          testId="quote-team-phone"
        />
        <EmailListField
          label="Quote Team Emails"
          description="Email addresses for quotation notifications"
          emails={settings.quote_team_emails}
          onAdd={v => addToList('quote_team_emails', v)}
          onRemove={i => removeFromList('quote_team_emails', i)}
          testIdPrefix="quote-team-email"
        />
      </div>

      {/* Backend / Office Team */}
      <div className="bg-white border rounded-lg p-6 space-y-5">
        <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
          <Phone className="h-4 w-4 text-slate-400" />
          Backend / Office Team
        </h2>
        <PhoneField
          label="Backend Team WhatsApp Number"
          description="WhatsApp number for general ticket update notifications"
          value={settings.backend_team_phone}
          onChange={v => updateField('backend_team_phone', v)}
          testId="backend-team-phone"
        />
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
