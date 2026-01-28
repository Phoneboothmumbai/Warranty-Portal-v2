import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const EngineerAuthContext = createContext();

export const useEngineerAuth = () => useContext(EngineerAuthContext);

export const EngineerAuthProvider = ({ children }) => {
  const [engineer, setEngineer] = useState(() => {
    const storedEngineer = localStorage.getItem('engineer_data');
    const storedToken = localStorage.getItem('engineer_token');
    return storedEngineer && storedToken ? JSON.parse(storedEngineer) : null;
  });
  const [token, setToken] = useState(localStorage.getItem('engineer_token'));
  const [loading, setLoading] = useState(false);

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
