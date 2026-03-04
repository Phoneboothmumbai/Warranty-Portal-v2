import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { Shield, LayoutDashboard, Wrench, Laptop, FileText, BarChart3, User, LogOut, AlertTriangle } from 'lucide-react';

const PortalLayout = () => {
  const { tenant, user, isAuthenticated, logout, loading, error, tenantCode } = useTenant();
  const navigate = useNavigate();

  if (loading) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
      <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin" />
      <p className="mt-4 text-sm text-slate-500">Loading portal...</p>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center p-8 max-w-sm">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h1 className="text-xl font-bold text-slate-800 mb-2">Portal Not Found</h1>
        <p className="text-sm text-slate-500">The portal "{tenantCode}" doesn't exist or is not active.</p>
      </div>
    </div>
  );

  if (!isAuthenticated) {
    return <Outlet />;
  }

  const primaryColor = tenant?.portal_theme?.primary_color || tenant?.accent_color || '#0F62FE';

  const navItems = [
    { path: `/portal/${tenantCode}`, label: 'Dashboard', icon: BarChart3, end: true },
    { path: `/portal/${tenantCode}/tickets`, label: 'Tickets', icon: Wrench },
    { path: `/portal/${tenantCode}/devices`, label: 'Devices', icon: Laptop },
    { path: `/portal/${tenantCode}/contracts`, label: 'Contracts', icon: FileText },
    { path: `/portal/${tenantCode}/profile`, label: 'Profile', icon: User },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Bar */}
      <header className="bg-white border-b sticky top-0 z-50">
        <div className="flex items-center h-14 px-4 lg:px-6">
          <div className="flex items-center gap-2.5 mr-6 shrink-0">
            {tenant?.logo_url ? (
              <img src={tenant.logo_url} alt="" className="h-7 w-auto" />
            ) : (
              <div className="h-7 w-7 rounded-md flex items-center justify-center" style={{ backgroundColor: primaryColor }}>
                <Shield className="h-4 w-4 text-white" />
              </div>
            )}
            <div>
              <span className="font-semibold text-slate-900 text-sm block leading-tight">{tenant?.company_name}</span>
              <span className="text-[10px] text-slate-400">Powered by {tenant?.provider_name || 'aftersales.support'}</span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-0.5 flex-1" data-testid="portal-nav">
            {navItems.map(item => (
              <NavLink key={item.path} to={item.path} end={item.end}
                className={({ isActive }) => `flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md transition-all ${
                  isActive ? 'text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
                style={({ isActive }) => isActive ? { backgroundColor: primaryColor } : {}}
                data-testid={`portal-nav-${item.label.toLowerCase()}`}
              >
                <item.icon className="w-4 h-4" />{item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3 ml-auto">
            <div className="hidden sm:flex items-center gap-2">
              <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ backgroundColor: primaryColor + '20' }}>
                <span className="text-xs font-semibold" style={{ color: primaryColor }}>{user?.name?.charAt(0).toUpperCase() || 'U'}</span>
              </div>
              <span className="text-xs text-slate-600">{user?.name}</span>
            </div>
            <button onClick={() => { logout(); navigate(`/portal/${tenantCode}`); }}
              className="text-slate-400 hover:text-red-500 transition-colors" data-testid="portal-logout">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Mobile Nav */}
        <div className="md:hidden overflow-x-auto flex items-center gap-1 px-4 pb-2">
          {navItems.map(item => (
            <NavLink key={item.path} to={item.path} end={item.end}
              className={({ isActive }) => `flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md whitespace-nowrap ${
                isActive ? 'text-white' : 'text-slate-500 hover:bg-slate-100'
              }`}
              style={({ isActive }) => isActive ? { backgroundColor: primaryColor } : {}}
            >
              <item.icon className="w-3.5 h-3.5" />{item.label}
            </NavLink>
          ))}
        </div>
      </header>

      <main className="flex-1 p-5 lg:p-7">
        <Outlet />
      </main>

      <footer className="border-t py-3 px-6 text-center text-xs text-slate-400">
        {tenant?.provider_name || 'aftersales.support'} Customer Portal
      </footer>
    </div>
  );
};

export default PortalLayout;
