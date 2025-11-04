import React, { createContext, useState, useContext, useEffect } from 'react';
import { getCurrentUser } from '../services/api';
import wsService from '../services/websocket';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await getCurrentUser();
        setUser(response.data.user);
        wsService.connect(token);
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  };

  const loginUser = (userData, token) => {
    localStorage.setItem('token', token);
    setUser(userData);
    wsService.connect(token);
  };

  const logoutUser = () => {
    localStorage.removeItem('token');
    setUser(null);
    wsService.disconnect();
  };

  return (
    <AuthContext.Provider value={{ user, loading, loginUser, logoutUser }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};