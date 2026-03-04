import { useTenant } from '../../context/TenantContext';
import { User, Mail, Building2, Shield } from 'lucide-react';

export default function PortalProfile() {
  const { tenant, user, tenantCode, logout } = useTenant();
  const primary = tenant?.portal_theme?.primary_color || '#0F62FE';

  return (
    <div className="space-y-4 max-w-lg" data-testid="portal-profile">
      <h1 className="text-xl font-bold text-slate-900">Your Profile</h1>

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
            <span className="text-slate-500 w-20">Name</span>
            <span className="text-slate-700 font-medium">{user?.name || '-'}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Mail className="w-4 h-4 text-slate-400" />
            <span className="text-slate-500 w-20">Email</span>
            <span className="text-slate-700 font-medium">{user?.email || '-'}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Building2 className="w-4 h-4 text-slate-400" />
            <span className="text-slate-500 w-20">Company</span>
            <span className="text-slate-700 font-medium">{tenant?.company_name || '-'}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Shield className="w-4 h-4 text-slate-400" />
            <span className="text-slate-500 w-20">Portal</span>
            <span className="text-slate-700 font-medium">{tenantCode}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
