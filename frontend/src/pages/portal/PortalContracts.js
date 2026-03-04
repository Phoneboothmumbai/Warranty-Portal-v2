import { useState, useEffect } from 'react';
import { useTenant } from '../../context/TenantContext';
import { FileText, Shield, Clock, CheckCircle, XCircle } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PortalContracts() {
  const { tenant, tenantCode } = useTenant();
  const [contracts, setContracts] = useState([]);
  const [stats, setStats] = useState({ total: 0, active: 0, expired: 0 });
  const [loading, setLoading] = useState(true);
  const primary = tenant?.portal_theme?.primary_color || tenant?.accent_color || '#0F62FE';

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/contracts`);
        if (res.ok) {
          const d = await res.json();
          setContracts(d.contracts || []);
          setStats({ total: d.total || 0, active: d.active || 0, expired: d.expired || 0 });
        }
      } catch { /* */ }
      finally { setLoading(false); }
    })();
  }, [tenantCode]);

  if (loading) return (
    <div className="flex items-center justify-center h-40">
      <div className="w-6 h-6 border-3 border-t-transparent rounded-full animate-spin" style={{ borderColor: primary }} />
    </div>
  );

  return (
    <div className="space-y-4" data-testid="portal-contracts">
      <h1 className="text-xl font-bold text-slate-900">Service Contracts</h1>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">Total Contracts</p>
          <p className="text-2xl font-bold text-slate-800">{stats.total}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">Active</p>
          <p className="text-2xl font-bold text-emerald-600">{stats.active}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-slate-500">Expired</p>
          <p className="text-2xl font-bold text-red-600">{stats.expired}</p>
        </div>
      </div>

      {/* Contract List */}
      {contracts.length > 0 ? (
        <div className="space-y-3">
          {contracts.map(c => (
            <div key={c.id} className="bg-white rounded-lg border p-4 hover:border-slate-300 transition-colors" data-testid={`portal-contract-${c.id}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-slate-800">{c.name}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-xs border font-medium inline-flex items-center gap-1 ${
                      c.status === 'active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-700 border-red-200'
                    }`}>
                      {c.status === 'active' ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                      {c.status}
                    </span>
                  </div>
                  {c.contract_number && <p className="text-xs text-slate-400 mt-0.5">#{c.contract_number}</p>}
                </div>
                {c.type && <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">{c.type}</span>}
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div>
                  <p className="text-xs text-slate-400">Start Date</p>
                  <p className="text-slate-700 font-medium">{(c.start_date || '').slice(0, 10) || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">End Date</p>
                  <p className="text-slate-700 font-medium">{(c.end_date || '').slice(0, 10) || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Devices Covered</p>
                  <p className="text-slate-700 font-medium">{c.device_count}</p>
                </div>
                {c.coverage && (
                  <div>
                    <p className="text-xs text-slate-400">Coverage</p>
                    <p className="text-slate-700 font-medium capitalize">{c.coverage}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg border p-12 text-center">
          <FileText className="w-10 h-10 mx-auto mb-3" style={{ color: primary + '60' }} />
          <p className="text-sm text-slate-500">No service contracts found. Contact your service provider to set up an AMC or warranty plan.</p>
        </div>
      )}
    </div>
  );
}
