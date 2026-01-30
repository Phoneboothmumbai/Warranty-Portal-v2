import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [admin, setAdmin] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('admin_token'));
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  const logout = useCallback(() => {
    localStorage.removeItem('admin_token');
    setToken(null);
    setAdmin(null);
    setAuthError(null);
  }, []);

  const fetchAdmin = useCallback(async (currentToken) => {
    if (!currentToken) {
      setLoading(false);
      return;
    }
    
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${currentToken}` },
        timeout: 10000 // 10 second timeout
      });
      setAdmin(response.data);
      setAuthError(null);
    } catch (error) {
      console.error('Auth error:', error);
      
      // Only logout on 401 (unauthorized) or 403 (forbidden)
      // Don't logout on network errors, CORS issues, or server errors
      if (error.response && (error.response.status === 401 || error.response.status === 403)) {
        logout();
      } else {
        // Network error, server error, or CORS - keep token but show error
        setAuthError('Unable to verify authentication. Please check your connection.');
        // Still try to show admin panel if we have a valid token structure
        try {
          const tokenPayload = JSON.parse(atob(currentToken.split('.')[1]));
          if (tokenPayload.exp * 1000 > Date.now()) {
            // Token is not expired, set minimal admin info
            setAdmin({ email: tokenPayload.sub, name: 'Admin' });
          } else {
            logout();
          }
        } catch (e) {
          // Invalid token structure
          logout();
        }
      }
    } finally {
      setLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    fetchAdmin(token);
  }, [token, fetchAdmin]);

  const login = async (email, password, tenantSlug = null) => {
    // Build URL with tenant context if provided
    let url = `${API}/auth/login`;
    if (tenantSlug) {
      url += `?_tenant=${tenantSlug}`;
    }
    
    const response = await axios.post(url, { email, password });
    const { access_token, tenant } = response.data;
    localStorage.setItem('admin_token', access_token);
    
    // Store tenant info if returned
    if (tenant) {
      localStorage.setItem('admin_tenant', JSON.stringify(tenant));
    }
    
    setToken(access_token);
    setAuthError(null);
    return response.data;
  };

  const value = {
    admin,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!admin,
    authError
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
