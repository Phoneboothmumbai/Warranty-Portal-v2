import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, Laptop, Shield, FileText, Ticket, Package, 
  Users, MapPin, User, LogOut, Menu, X, ChevronDown, Building2, ShoppingBag, Key, Inbox
} from 'lucide-react';
import { useCompanyAuth } from '../context/CompanyAuthContext';

const navItems = [
  { to: '/company/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/company/devices', icon: Laptop, label: 'Devices' },
  { to: '/company/support-tickets', icon: Inbox, label: 'Support Tickets' },
  { to: '/company/credentials', icon: Key, label: 'Credentials' },
  { to: '/company/warranty', icon: Shield, label: 'Warranty & Coverage' },
  { to: '/company/amc', icon: FileText, label: 'AMC / Contracts' },
  { to: '/company/amc-requests', icon: FileText, label: 'Request AMC' },
  { to: '/company/tickets', icon: Ticket, label: 'Service Requests' },
  { to: '/company/office-supplies', icon: ShoppingBag, label: 'Office Supplies' },
  { to: '/company/deployments', icon: Package, label: 'Deployments' },
  { to: '/company/users', icon: Users, label: 'Users / Contacts' },
  { to: '/company/sites', icon: MapPin, label: 'Sites' },
  { to: '/company/profile', icon: User, label: 'Profile' },
];

const CompanyLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const { user, token, logout, loading } = useCompanyAuth();
  const navigate = useNavigate();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !token) {
      navigate('/company/login');
    }
  }, [token, loading, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/company/login');
  };

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Don't render if not authenticated
  if (!token) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 transform transition-transform duration-200 lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 h-16 px-6 border-b border-slate-100">
            <div className="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center">
              <Building2 className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-slate-900 text-sm">Company Portal</h1>
              <p className="text-xs text-slate-500 truncate max-w-[140px]">{user?.company_name}</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`
                  }
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>

          {/* User section */}
          <div className="p-3 border-t border-slate-100">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors"
            >
              <LogOut className="h-5 w-5" />
              Logout
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top header */}
        <header className="sticky top-0 z-30 bg-white border-b border-slate-200">
          <div className="flex items-center justify-between h-16 px-4 lg:px-8">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 -ml-2 rounded-lg hover:bg-slate-100"
            >
              <Menu className="h-5 w-5 text-slate-600" />
            </button>

            <div className="flex-1" />

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-50"
              >
                <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-emerald-700">
                    {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                  </span>
                </div>
                <div className="hidden sm:block text-left">
                  <p className="text-sm font-medium text-slate-900">{user?.name}</p>
                  <p className="text-xs text-slate-500 capitalize">{user?.role?.replace('_', ' ')}</p>
                </div>
                <ChevronDown className="h-4 w-4 text-slate-400" />
              </button>

              {userMenuOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setUserMenuOpen(false)} />
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-slate-200 py-1 z-20">
                    <NavLink
                      to="/company/profile"
                      onClick={() => setUserMenuOpen(false)}
                      className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      <User className="h-4 w-4" />
                      Profile
                    </NavLink>
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                    >
                      <LogOut className="h-4 w-4" />
                      Logout
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default CompanyLayout;
