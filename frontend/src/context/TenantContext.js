import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL;
const TenantContext = createContext(null);

export const TenantProvider = ({ children }) => {
  const { tenantCode } = useParams();
  const [tenant, setTenant] = useState(null);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem(`portal_token_${tenantCode}`));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!tenantCode) return;
    (async () => {
      try {
        const res = await fetch(`${API}/api/portal/tenant/${tenantCode}`);
        if (res.ok) { setTenant(await res.json()); setError(null); }
        else setError('Portal not found');
      } catch { setError('Connection error'); }
      finally { setLoading(false); }
    })();
  }, [tenantCode]);

  useEffect(() => {
    if (!token) { setUser(null); return; }
    (async () => {
      try {
        const res = await fetch(`${API}/api/company/auth/me`, { headers: { Authorization: `Bearer ${token}` } });
        if (res.ok) setUser(await res.json());
        else { localStorage.removeItem(`portal_token_${tenantCode}`); setToken(null); setUser(null); }
      } catch { /* ignore */ }
    })();
  }, [token, tenantCode]);

  const login = async (email, password) => {
    const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    localStorage.setItem(`portal_token_${tenantCode}`, data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    return data;
  };

  const logout = () => {
    localStorage.removeItem(`portal_token_${tenantCode}`);
    setToken(null);
    setUser(null);
  };

  const hdrs = useCallback(() => ({
    Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'
  }), [token]);

  return (
    <TenantContext.Provider value={{ tenant, user, token, loading, error, login, logout, hdrs, tenantCode, isAuthenticated: !!user }}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = () => useContext(TenantContext);
export default TenantContext;
