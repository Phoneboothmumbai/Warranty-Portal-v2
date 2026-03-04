import { useState, useEffect } from 'react';
import { useTenant } from '../../context/TenantContext';
import { Laptop, Search, Shield, AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-react';
import { Input } from '../../components/ui/input';

const API = process.env.REACT_APP_BACKEND_URL;

const warrantyBadge = (s) => {
  const map = {
    active: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    expiring: 'bg-amber-50 text-amber-700 border-amber-200',
    expired: 'bg-red-50 text-red-700 border-red-200',
  };
  return map[s] || 'bg-slate-50 text-slate-600 border-slate-200';
};

export default function PortalDevices() {
  const { tenant, tenantCode } = useTenant();
  const [devices, setDevices] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [warrantyFilter, setWarrantyFilter] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const primary = tenant?.portal_theme?.primary_color || tenant?.accent_color || '#0F62FE';
  const limit = 25;

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ page, limit });
        if (search) params.set('search', search);
        if (warrantyFilter) params.set('warranty', warrantyFilter);
        const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/devices?${params}`);
        if (res.ok) {
          const d = await res.json();
          setDevices(d.devices || []);
          setTotal(d.total || 0);
        }
      } catch { /* */ }
      finally { setLoading(false); }
    })();
  }, [tenantCode, page, search, warrantyFilter]);

  const totalPages = Math.ceil(total / limit);

  // Count warranty statuses from loaded data
  const activeCount = devices.filter(d => d.warranty_status === 'active').length;
  const expiringCount = devices.filter(d => d.warranty_status === 'expiring').length;
  const expiredCount = devices.filter(d => d.warranty_status === 'expired').length;

  return (
    <div className="space-y-4" data-testid="portal-devices">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Your Devices</h1>
          <p className="text-sm text-slate-500">{total} device{total !== 1 ? 's' : ''} registered</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <Input className="pl-9 w-56" placeholder="Search devices..."
              value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
              data-testid="portal-device-search" />
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-lg border p-4 cursor-pointer hover:border-slate-300 transition-colors" onClick={() => setWarrantyFilter('')}
          data-testid="portal-devices-total">
          <p className="text-xs text-slate-500">Total Devices</p>
          <p className="text-2xl font-bold text-slate-800">{total}</p>
        </div>
        <div className="bg-white rounded-lg border p-4 cursor-pointer hover:border-emerald-300 transition-colors" onClick={() => setWarrantyFilter(warrantyFilter === 'active' ? '' : 'active')}
          style={warrantyFilter === 'active' ? { borderColor: '#22C55E' } : {}}>
          <p className="text-xs text-slate-500">Under Warranty</p>
          <p className="text-2xl font-bold text-emerald-600">{activeCount}</p>
        </div>
        <div className="bg-white rounded-lg border p-4 cursor-pointer hover:border-red-300 transition-colors" onClick={() => setWarrantyFilter(warrantyFilter === 'expired' ? '' : 'expired')}
          style={warrantyFilter === 'expired' ? { borderColor: '#DC2626' } : {}}>
          <p className="text-xs text-slate-500">Expired</p>
          <p className="text-2xl font-bold text-red-600">{expiredCount}</p>
        </div>
        <div className="bg-white rounded-lg border p-4 cursor-pointer hover:border-amber-300 transition-colors" onClick={() => setWarrantyFilter(warrantyFilter === 'expiring' ? '' : 'expiring')}
          style={warrantyFilter === 'expiring' ? { borderColor: '#F59E0B' } : {}}>
          <p className="text-xs text-slate-500">Expiring Soon</p>
          <p className="text-2xl font-bold text-amber-600">{expiringCount}</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-3 border-t-transparent rounded-full animate-spin" style={{ borderColor: primary }} />
        </div>
      ) : devices.length > 0 ? (
        <>
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead><tr className="border-b bg-slate-50">
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Serial #</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Brand / Model</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 hidden md:table-cell">Type</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 hidden lg:table-cell">Site</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 hidden lg:table-cell">Assigned To</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Warranty</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 hidden md:table-cell">Expires</th>
              </tr></thead>
              <tbody>
                {devices.map(d => (
                  <tr key={d.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-slate-600">{d.serial_number || '-'}</td>
                    <td className="py-3 px-4">
                      <span className="font-medium text-slate-700">{d.brand}</span>
                      {d.model && <span className="text-slate-400 ml-1 text-xs">{d.model}</span>}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500 capitalize hidden md:table-cell">{d.device_type || '-'}</td>
                    <td className="py-3 px-4 text-xs text-slate-500 hidden lg:table-cell">{d.site_name || '-'}</td>
                    <td className="py-3 px-4 text-xs text-slate-500 hidden lg:table-cell">{d.assigned_user || '-'}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs border capitalize ${warrantyBadge(d.warranty_status)}`}>
                        {d.warranty_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-400 hidden md:table-cell">{(d.warranty_end_date || '').slice(0, 10) || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-500">Page {page} of {totalPages}</p>
              <div className="flex items-center gap-1">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                  className="p-1.5 rounded border text-slate-500 hover:bg-slate-50 disabled:opacity-30">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                  className="p-1.5 rounded border text-slate-500 hover:bg-slate-50 disabled:opacity-30">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white rounded-lg border p-12 text-center">
          <Laptop className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500">{search ? 'No devices match your search' : 'No devices registered'}</p>
        </div>
      )}

      {(expiredCount > 0 || expiringCount > 0) && !warrantyFilter && (
        <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-100 rounded-lg text-sm">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <span className="text-amber-800">
            {expiredCount > 0 && `${expiredCount} device(s) out of warranty. `}
            {expiringCount > 0 && `${expiringCount} device(s) expiring soon. `}
            Contact your service provider for AMC coverage.
          </span>
        </div>
      )}
    </div>
  );
}
