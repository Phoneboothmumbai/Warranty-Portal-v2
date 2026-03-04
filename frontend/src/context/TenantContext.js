import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL;
const TenantContext = createContext(null);

export const TenantProvider = ({ children }) => {
  const { tenantCode } = useParams();
  const storageKey = `portal_${tenantCode}`;
  const [tenant, setTenant] = useState(null);
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem(`${storageKey}_user`)); } catch { return null; }
  });
  const [token, setToken] = useState(() => localStorage.getItem(`${storageKey}_token`));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Resolve tenant
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

  const login = async (email, password) => {
    const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    localStorage.setItem(`${storageKey}_token`, data.access_token);
    localStorage.setItem(`${storageKey}_user`, JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data;
  };

  const logout = () => {
    localStorage.removeItem(`${storageKey}_token`);
    localStorage.removeItem(`${storageKey}_user`);
    setToken(null);
    setUser(null);
  };

  const hdrs = useCallback(() => ({
    Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'
  }), [token]);

  return (
    <TenantContext.Provider value={{ tenant, user, token, loading, error, login, logout, hdrs, tenantCode, isAuthenticated: !!user && !!token }}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = () => useContext(TenantContext) || {};

// Utility functions for admin pages (pass-through since admin doesn't use tenant routing)
export const buildTenantUrl = (path) => path;
export const getTenantRequestConfig = () => ({});

export default TenantContext;
