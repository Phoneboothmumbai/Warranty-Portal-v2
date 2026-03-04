import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Save, Mail, Phone, X, Truck, Lock, Plus, Trash2 } from 'lucide-react';
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

const TravelCostConfig = ({ token }) => {
  const [config, setConfig] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/analytics/service-cost-config`, { headers: { Authorization: `Bearer ${token}` } });
        setConfig(res.data);
      } catch { setConfig({ travel_tiers: [{ name: 'Local', min_km: 0, max_km: 15, cost: 200 }, { name: 'City', min_km: 15, max_km: 30, cost: 400 }, { name: 'Outstation', min_km: 30, max_km: 50, cost: 700 }, { name: 'Long Distance', min_km: 50, max_km: 9999, cost: 1200 }], default_hourly_rate: 500, per_km_rate: 10 }); }
    })();
  }, [token]);

  const save = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/analytics/service-cost-config`, config, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Service cost config saved');
    } catch { toast.error('Failed to save'); }
    finally { setSaving(false); }
  };

  const updateTier = (i, key, val) => {
    const tiers = [...config.travel_tiers];
    tiers[i] = { ...tiers[i], [key]: key === 'name' ? val : parseFloat(val) || 0 };
    setConfig(c => ({ ...c, travel_tiers: tiers }));
  };

  const addTier = () => setConfig(c => ({ ...c, travel_tiers: [...c.travel_tiers, { name: 'New Zone', min_km: 0, max_km: 0, cost: 0 }] }));
  const removeTier = i => setConfig(c => ({ ...c, travel_tiers: c.travel_tiers.filter((_, idx) => idx !== i) }));

  if (!config) return null;

  return (
    <div className="bg-white border rounded-lg p-6 space-y-5" data-testid="travel-cost-config">
      <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
        <Truck className="h-4 w-4 text-slate-400" />
        Service Cost Configuration
      </h2>
      <p className="text-xs text-slate-400">Configure travel cost zones and default engineer rates for profitability calculations</p>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium block mb-1">Default Hourly Rate (INR/hr)</label>
          <Input type="number" value={config.default_hourly_rate} onChange={e => setConfig(c => ({ ...c, default_hourly_rate: parseFloat(e.target.value) || 0 }))} placeholder="500" data-testid="default-hourly-rate" />
          <p className="text-xs text-slate-400 mt-1">Used when engineer has no hourly rate set</p>
        </div>
        <div>
          <label className="text-sm font-medium block mb-1">Per KM Rate (INR)</label>
          <Input type="number" value={config.per_km_rate} onChange={e => setConfig(c => ({ ...c, per_km_rate: parseFloat(e.target.value) || 0 }))} placeholder="10" data-testid="per-km-rate" />
          <p className="text-xs text-slate-400 mt-1">Used for exact distance-based calculations</p>
        </div>
      </div>
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium">Travel Cost Zones</label>
          <Button variant="outline" size="sm" onClick={addTier} data-testid="add-travel-tier"><Plus className="w-3 h-3 mr-1" />Add Zone</Button>
        </div>
        <div className="space-y-2">
          {config.travel_tiers.map((tier, i) => (
            <div key={i} className="flex items-center gap-2 bg-slate-50 p-2 rounded" data-testid={`travel-tier-${i}`}>
              <Input className="w-32" value={tier.name} onChange={e => updateTier(i, 'name', e.target.value)} placeholder="Zone name" />
              <Input className="w-20" type="number" value={tier.min_km} onChange={e => updateTier(i, 'min_km', e.target.value)} placeholder="Min" />
              <span className="text-xs text-slate-400">to</span>
              <Input className="w-20" type="number" value={tier.max_km} onChange={e => updateTier(i, 'max_km', e.target.value)} placeholder="Max" />
              <span className="text-xs text-slate-400">km</span>
              <span className="text-xs text-slate-500">INR</span>
              <Input className="w-24" type="number" value={tier.cost} onChange={e => updateTier(i, 'cost', e.target.value)} placeholder="Cost" />
              <button onClick={() => removeTier(i)} className="text-red-400 hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
            </div>
          ))}
        </div>
      </div>
      <Button onClick={save} disabled={saving} className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="save-cost-config">
        {saving ? 'Saving...' : <><Save className="h-4 w-4 mr-2" />Save Cost Config</>}
      </Button>
    </div>
  );
};

const ProfitabilityPasswordConfig = ({ token }) => {
  const [pw, setPw] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (pw.length < 4) { toast.error('Password must be at least 4 characters'); return; }
    if (pw !== confirm) { toast.error('Passwords do not match'); return; }
    setSaving(true);
    try {
      await axios.post(`${API}/analytics/profitability-password`, { password: pw }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Profitability password set');
      setPw(''); setConfirm('');
    } catch { toast.error('Failed to set password'); }
    finally { setSaving(false); }
  };

  return (
    <div className="bg-white border rounded-lg p-6 space-y-5" data-testid="profitability-password-config">
      <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
        <Lock className="h-4 w-4 text-slate-400" />
        Profitability Access Password
      </h2>
      <p className="text-xs text-slate-400">Set a password to protect the Profitability tab in Analytics. Only owners with this password can view cost & profit data.</p>
      <div className="grid grid-cols-2 gap-4 max-w-lg">
        <div>
          <label className="text-sm font-medium block mb-1">New Password</label>
          <Input type="password" value={pw} onChange={e => setPw(e.target.value)} placeholder="Set password" data-testid="profitability-pw" />
        </div>
        <div>
          <label className="text-sm font-medium block mb-1">Confirm Password</label>
          <Input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="Confirm" data-testid="profitability-pw-confirm" />
        </div>
      </div>
      <Button onClick={save} disabled={saving} variant="outline" data-testid="save-profitability-pw">
        {saving ? 'Setting...' : <><Lock className="h-4 w-4 mr-2" />Set Password</>}
      </Button>
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

      {/* Travel Cost Tiers */}
      <TravelCostConfig token={token} />

      {/* Profitability Password */}
      <ProfitabilityPasswordConfig token={token} />

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
