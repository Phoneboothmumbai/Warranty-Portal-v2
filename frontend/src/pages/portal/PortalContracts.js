import { useState, useEffect } from 'react';
import { useTenant } from '../../context/TenantContext';
import { FileText, Shield, Clock } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PortalContracts() {
  const { tenant, tenantCode } = useTenant();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const primary = tenant?.portal_theme?.primary_color || '#0F62FE';

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/analytics?days=365`);
        if (res.ok) setData(await res.json());
      } catch { /* */ }
      finally { setLoading(false); }
    })();
  }, [tenantCode]);

  if (loading) return <div className="flex items-center justify-center h-40"><div className="w-6 h-6 border-3 border-t-transparent rounded-full animate-spin" style={{ borderColor: primary }} /></div>;

  const s = data?.summary || {};

  return (
    <div className="space-y-4" data-testid="portal-contracts">
      <h1 className="text-xl font-bold text-slate-900">Service Contracts</h1>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">Active Contracts</p>
          <p className="text-2xl font-bold text-emerald-600">{s.active_contracts || 0}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">Devices Covered</p>
          <p className="text-2xl font-bold text-slate-800">{s.active_warranty || 0}</p>
          <p className="text-xs text-slate-400">of {s.total_devices || 0} total</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">SLA Compliance</p>
          <p className="text-2xl font-bold" style={{ color: primary }}>{s.sla_compliance || 0}%</p>
        </div>
      </div>

      <div className="bg-white rounded-lg border p-6 text-center">
        <FileText className="w-10 h-10 mx-auto mb-3" style={{ color: primary + '60' }} />
        <p className="text-sm text-slate-500">
          {s.active_contracts > 0
            ? `You have ${s.active_contracts} active service contract(s). Contact your service provider for detailed contract information.`
            : 'No active contracts found. Contact your service provider to set up an AMC or warranty plan.'}
        </p>
      </div>
    </div>
  );
}
