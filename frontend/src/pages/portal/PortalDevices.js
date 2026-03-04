import { useState, useEffect } from 'react';
import { useTenant } from '../../context/TenantContext';
import { Laptop, Search, Shield, AlertTriangle } from 'lucide-react';
import { Input } from '../../components/ui/input';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PortalDevices() {
  const { tenant, tenantCode } = useTenant();
  const [devices, setDevices] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const primary = tenant?.portal_theme?.primary_color || '#0F62FE';

  useEffect(() => {
    (async () => {
      try {
        // Fetch from company analytics for device data
        const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/analytics?days=365`);
        if (res.ok) {
          const d = await res.json();
          // We'll display the brand distribution and warranty timeline
          setDevices(d);
        }
      } catch { /* */ }
      finally { setLoading(false); }
    })();
  }, [tenantCode]);

  if (loading) return <div className="flex items-center justify-center h-40"><div className="w-6 h-6 border-3 border-t-transparent rounded-full animate-spin" style={{ borderColor: primary }} /></div>;

  const s = devices?.summary || {};

  return (
    <div className="space-y-4" data-testid="portal-devices">
      <h1 className="text-xl font-bold text-slate-900">Your Devices</h1>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">Total Devices</p>
          <p className="text-2xl font-bold text-slate-800">{s.total_devices || 0}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">Under Warranty</p>
          <p className="text-2xl font-bold text-emerald-600">{s.active_warranty || 0}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">Expired</p>
          <p className="text-2xl font-bold text-red-600">{s.expired_warranty || 0}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">Expiring Soon</p>
          <p className="text-2xl font-bold text-amber-600">{s.expiring_30d || 0}</p>
        </div>
      </div>

      {(devices?.brand_distribution || []).length > 0 && (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Devices by Brand</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {(devices.brand_distribution || []).map((b, i) => (
              <div key={i} className="flex items-center gap-2 p-2 bg-slate-50 rounded">
                <Laptop className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-700 font-medium">{b.name}</span>
                <span className="text-xs text-slate-400 ml-auto">{b.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {(s.expired_warranty > 0 || s.expiring_30d > 0) && (
        <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-100 rounded-lg text-sm">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <span className="text-amber-800">
            {s.expired_warranty > 0 && `${s.expired_warranty} device(s) out of warranty. `}
            {s.expiring_30d > 0 && `${s.expiring_30d} device(s) expiring soon. `}
            Contact your service provider for AMC coverage.
          </span>
        </div>
      )}
    </div>
  );
}
