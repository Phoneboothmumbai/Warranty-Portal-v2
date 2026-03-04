import { useState, useEffect } from 'react';
import { useTenant } from '../../context/TenantContext';
import { User, Mail, Building2, Shield, Phone, MapPin, Laptop, Wrench, FileText } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PortalProfile() {
  const { tenant, user, tenantCode, logout } = useTenant();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const primary = tenant?.portal_theme?.primary_color || tenant?.accent_color || '#0F62FE';

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/profile`);
        if (res.ok) setProfile(await res.json());
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
    <div className="space-y-4 max-w-2xl" data-testid="portal-profile">
      <h1 className="text-xl font-bold text-slate-900">Your Profile</h1>

      {/* User Card */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold text-white" style={{ backgroundColor: primary }}>
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-800">{user?.name || 'User'}</h2>
            <p className="text-sm text-slate-500">{user?.email}</p>
          </div>
        </div>

        <div className="space-y-3 border-t pt-4">
          <div className="flex items-center gap-3 text-sm">
            <User className="w-4 h-4 text-slate-400" />
            <span className="text-slate-500 w-24">Name</span>
            <span className="text-slate-700 font-medium">{user?.name || '-'}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Mail className="w-4 h-4 text-slate-400" />
            <span className="text-slate-500 w-24">Email</span>
            <span className="text-slate-700 font-medium">{user?.email || '-'}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Building2 className="w-4 h-4 text-slate-400" />
            <span className="text-slate-500 w-24">Company</span>
            <span className="text-slate-700 font-medium">{tenant?.company_name || '-'}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Shield className="w-4 h-4 text-slate-400" />
            <span className="text-slate-500 w-24">Portal</span>
            <span className="text-slate-700 font-medium">{tenantCode}</span>
          </div>
        </div>
      </div>

      {/* Company Details */}
      {profile && (
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Company Information</h3>
          <div className="space-y-3">
            {profile.contact_name && (
              <div className="flex items-center gap-3 text-sm">
                <User className="w-4 h-4 text-slate-400" />
                <span className="text-slate-500 w-24">Contact</span>
                <span className="text-slate-700">{profile.contact_name}</span>
              </div>
            )}
            {profile.contact_email && (
              <div className="flex items-center gap-3 text-sm">
                <Mail className="w-4 h-4 text-slate-400" />
                <span className="text-slate-500 w-24">Email</span>
                <span className="text-slate-700">{profile.contact_email}</span>
              </div>
            )}
            {profile.contact_phone && (
              <div className="flex items-center gap-3 text-sm">
                <Phone className="w-4 h-4 text-slate-400" />
                <span className="text-slate-500 w-24">Phone</span>
                <span className="text-slate-700">{profile.contact_phone}</span>
              </div>
            )}
            {(profile.address || profile.city) && (
              <div className="flex items-center gap-3 text-sm">
                <MapPin className="w-4 h-4 text-slate-400" />
                <span className="text-slate-500 w-24">Address</span>
                <span className="text-slate-700">{[profile.address, profile.city, profile.state, profile.pincode].filter(Boolean).join(', ')}</span>
              </div>
            )}
            {profile.gst_number && (
              <div className="flex items-center gap-3 text-sm">
                <FileText className="w-4 h-4 text-slate-400" />
                <span className="text-slate-500 w-24">GST</span>
                <span className="text-slate-700">{profile.gst_number}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stats */}
      {profile?.stats && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white rounded-lg border p-4 text-center">
            <Laptop className="w-5 h-5 mx-auto mb-1" style={{ color: primary }} />
            <p className="text-2xl font-bold text-slate-800">{profile.stats.devices}</p>
            <p className="text-xs text-slate-500">Devices</p>
          </div>
          <div className="bg-white rounded-lg border p-4 text-center">
            <Wrench className="w-5 h-5 mx-auto mb-1" style={{ color: primary }} />
            <p className="text-2xl font-bold text-slate-800">{profile.stats.tickets}</p>
            <p className="text-xs text-slate-500">Tickets</p>
          </div>
          <div className="bg-white rounded-lg border p-4 text-center">
            <FileText className="w-5 h-5 mx-auto mb-1" style={{ color: primary }} />
            <p className="text-2xl font-bold text-slate-800">{profile.stats.contracts}</p>
            <p className="text-xs text-slate-500">Contracts</p>
          </div>
        </div>
      )}

      {/* Logout */}
      <button onClick={logout}
        className="w-full py-2.5 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
        data-testid="portal-logout-btn">
        Sign Out
      </button>
    </div>
  );
}
