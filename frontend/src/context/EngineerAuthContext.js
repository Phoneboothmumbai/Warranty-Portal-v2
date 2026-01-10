import { createContext, useContext, useState, useEffect } from 'react';

const EngineerAuthContext = createContext();

export const useEngineerAuth = () => useContext(EngineerAuthContext);

export const EngineerAuthProvider = ({ children }) => {
  const [engineer, setEngineer] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('engineer_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedEngineer = localStorage.getItem('engineer_data');
    if (storedEngineer && token) {
      setEngineer(JSON.parse(storedEngineer));
    }
    setLoading(false);
  }, [token]);

  const login = (engineerData, accessToken) => {
    localStorage.setItem('engineer_token', accessToken);
    localStorage.setItem('engineer_data', JSON.stringify(engineerData));
    setToken(accessToken);
    setEngineer(engineerData);
  };

  const logout = () => {
    localStorage.removeItem('engineer_token');
    localStorage.removeItem('engineer_data');
    setToken(null);
    setEngineer(null);
  };

  return (
    <EngineerAuthContext.Provider value={{ engineer, token, loading, login, logout, isAuthenticated: !!token }}>
      {children}
    </EngineerAuthContext.Provider>
  );
};
