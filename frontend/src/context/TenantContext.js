import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Tenant context shape
const TenantContext = createContext({
  tenant: null,
  loading: true,
  error: null,
  resolution: null,
  refreshTenant: () => {},
});

/**
 * Extract tenant slug from current URL
 * Supports:
 * - Subdomain: acme.assetvault.io → acme
 * - Query param: localhost:3000?_tenant=acme → acme (dev only)
 */
function extractTenantFromUrl() {
  const hostname = window.location.hostname;
  const searchParams = new URLSearchParams(window.location.search);
  
  // 1. Check query param first (development fallback)
  const queryTenant = searchParams.get('_tenant');
  if (queryTenant) {
    return { slug: queryTenant, method: 'query_param' };
  }
  
  // 2. Check for subdomain
  // Skip for localhost, 127.0.0.1, and IP addresses
  if (hostname === 'localhost' || hostname === '127.0.0.1' || /^\d+\.\d+\.\d+\.\d+$/.test(hostname)) {
    return { slug: null, method: null };
  }
  
  // For preview.emergentagent.com domains
  // mspportal.preview.emergentagent.com → no tenant
  // acme.mspportal.preview.emergentagent.com → acme
  if (hostname.includes('.preview.emergentagent.com')) {
    const parts = hostname.replace('.preview.emergentagent.com', '').split('.');
    if (parts.length > 1) {
      return { slug: parts[0], method: 'subdomain' };
    }
    return { slug: null, method: null };
  }
  
  // Standard subdomain extraction
  const parts = hostname.split('.');
  if (parts.length >= 3) {
    const subdomain = parts[0];
    // Skip common non-tenant subdomains
    const skipSubdomains = ['www', 'app', 'api', 'admin', 'platform', 'mail', 'ftp'];
    if (!skipSubdomains.includes(subdomain)) {
      return { slug: subdomain, method: 'subdomain' };
    }
  }
  
  return { slug: null, method: null };
}

/**
 * Check if current route is a platform admin route
 */
function isPlatformRoute() {
  return window.location.pathname.startsWith('/platform');
}

/**
 * Check if current route is a public route that doesn't need tenant
 */
function isPublicRoute() {
  const publicPaths = [
    '/',
    '/features',
    '/pricing',
    '/about',
    '/contact',
    '/signup',
    '/privacy',
    '/terms',
    '/platform',
  ];
  
  const path = window.location.pathname;
  return publicPaths.some(p => path === p || path.startsWith(p + '/'));
}

export function TenantProvider({ children }) {
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [resolution, setResolution] = useState(null);

  const fetchTenantContext = useCallback(async () => {
    // Skip tenant resolution for platform routes
    if (isPlatformRoute()) {
      setLoading(false);
      setResolution('platform_route');
      return;
    }
    
    // Skip for public routes without tenant context
    const { slug, method } = extractTenantFromUrl();
    
    if (!slug && isPublicRoute()) {
      setLoading(false);
      setResolution('public_route');
      return;
    }

    try {
      setLoading(true);
      
      // Build request with tenant context
      const headers = {};
      let url = `${API}/api/tenant/context`;
      
      if (slug && method === 'query_param') {
        url += `?_tenant=${slug}`;
      } else if (slug && method === 'subdomain') {
        headers['X-Tenant-Slug'] = slug;
      }
      
      const response = await axios.get(url, { headers });
      
      if (response.data.tenant) {
        setTenant(response.data.tenant);
        setResolution(response.data.resolution);
        
        // Check if tenant is suspended
        if (response.data.tenant.status === 'suspended') {
          setError({ type: 'suspended', message: 'This workspace has been suspended.' });
        }
      } else if (slug) {
        // Tenant slug was provided but not found
        setError({ type: 'not_found', message: 'Workspace not found.' });
      }
    } catch (err) {
      console.error('Failed to fetch tenant context:', err);
      if (err.response?.status === 403) {
        setError({ type: 'suspended', message: err.response.data?.message || 'Workspace suspended.' });
      } else if (err.response?.status === 404) {
        setError({ type: 'not_found', message: 'Workspace not found.' });
      } else {
        setError({ type: 'error', message: 'Failed to load workspace.' });
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTenantContext();
  }, [fetchTenantContext]);

  // Apply tenant branding to document
  useEffect(() => {
    if (tenant?.branding) {
      const { accent_color, company_name, favicon_url, custom_css } = tenant.branding;
      
      // Set accent color CSS variable
      if (accent_color) {
        document.documentElement.style.setProperty('--tenant-accent-color', accent_color);
      }
      
      // Set page title
      document.title = 'aftersales.support';
      
      // Set favicon
      if (favicon_url) {
        let link = document.querySelector("link[rel~='icon']");
        if (!link) {
          link = document.createElement('link');
          link.rel = 'icon';
          document.head.appendChild(link);
        }
        link.href = favicon_url;
      }
      
      // Inject custom CSS
      if (custom_css) {
        let style = document.getElementById('tenant-custom-css');
        if (!style) {
          style = document.createElement('style');
          style.id = 'tenant-custom-css';
          document.head.appendChild(style);
        }
        style.textContent = custom_css;
      }
    }
  }, [tenant]);

  const value = {
    tenant,
    loading,
    error,
    resolution,
    refreshTenant: fetchTenantContext,
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
}

/**
 * Get tenant context for API calls
 * Returns headers and query params to include tenant context
 */
export function getTenantRequestConfig() {
  const { slug, method } = extractTenantFromUrl();
  
  const config = { headers: {}, params: {} };
  
  if (slug) {
    if (method === 'query_param') {
      config.params._tenant = slug;
    } else if (method === 'subdomain') {
      config.headers['X-Tenant-Slug'] = slug;
    }
  }
  
  return config;
}

/**
 * Build URL with tenant context preserved
 */
export function buildTenantUrl(path) {
  const { slug, method } = extractTenantFromUrl();
  
  if (method === 'query_param' && slug) {
    const separator = path.includes('?') ? '&' : '?';
    return `${path}${separator}_tenant=${slug}`;
  }
  
  return path;
}

export default TenantContext;
