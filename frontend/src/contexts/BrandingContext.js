import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const BrandingContext = createContext(null);

export function BrandingProvider({ children }) {
  const [branding, setBranding] = useState({
    accent_color: '#0F62FE',
    company_name: 'Warranty Portal',
    logo_url: null,
    logo_base64: null
  });
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrganizationBranding();
  }, []);

  const fetchOrganizationBranding = async () => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/api/org/current`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const org = response.data;
      setOrganization(org);
      
      if (org.branding) {
        setBranding(prev => ({
          ...prev,
          ...org.branding,
          company_name: org.branding.company_name || org.name || prev.company_name
        }));
      }
      
      // Apply accent color as CSS variable
      if (org.branding?.accent_color) {
        document.documentElement.style.setProperty('--accent-color', org.branding.accent_color);
        document.documentElement.style.setProperty('--accent-color-dark', adjustColor(org.branding.accent_color, -20));
        document.documentElement.style.setProperty('--accent-color-light', adjustColor(org.branding.accent_color, 40));
      }
    } catch (error) {
      console.log('Failed to fetch organization branding');
    } finally {
      setLoading(false);
    }
  };

  const updateBranding = async (newBranding) => {
    const token = localStorage.getItem('admin_token');
    
    try {
      await axios.put(`${API}/api/org/current/branding`, newBranding, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setBranding(prev => ({ ...prev, ...newBranding }));
      
      // Update CSS variable
      if (newBranding.accent_color) {
        document.documentElement.style.setProperty('--accent-color', newBranding.accent_color);
        document.documentElement.style.setProperty('--accent-color-dark', adjustColor(newBranding.accent_color, -20));
        document.documentElement.style.setProperty('--accent-color-light', adjustColor(newBranding.accent_color, 40));
      }
      
      return true;
    } catch (error) {
      console.error('Failed to update branding:', error);
      return false;
    }
  };

  const refreshBranding = () => {
    fetchOrganizationBranding();
  };

  return (
    <BrandingContext.Provider value={{ 
      branding, 
      organization,
      loading, 
      updateBranding,
      refreshBranding 
    }}>
      {children}
    </BrandingContext.Provider>
  );
}

export function useBranding() {
  const context = useContext(BrandingContext);
  if (!context) {
    return {
      branding: {
        accent_color: '#0F62FE',
        company_name: 'Warranty Portal',
        logo_url: null
      },
      organization: null,
      loading: false,
      updateBranding: () => {},
      refreshBranding: () => {}
    };
  }
  return context;
}

// Helper function to adjust color brightness
function adjustColor(color, amount) {
  const clamp = (num) => Math.min(255, Math.max(0, num));
  
  // Remove # if present
  color = color.replace('#', '');
  
  // Parse RGB values
  const num = parseInt(color, 16);
  const r = clamp((num >> 16) + amount);
  const g = clamp(((num >> 8) & 0x00FF) + amount);
  const b = clamp((num & 0x0000FF) + amount);
  
  // Return hex color
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}

export default BrandingContext;
