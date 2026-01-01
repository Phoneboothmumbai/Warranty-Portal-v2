import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SettingsContext = createContext(null);

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState({
    logo_url: null,
    logo_base64: null,
    accent_color: '#0F62FE',
    company_name: 'Warranty Portal'
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPublicSettings();
  }, []);

  const fetchPublicSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings/public`);
      setSettings(response.data);
      // Apply accent color as CSS variable
      document.documentElement.style.setProperty('--accent', response.data.accent_color);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshSettings = async () => {
    await fetchPublicSettings();
  };

  const value = {
    settings,
    loading,
    refreshSettings
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};
