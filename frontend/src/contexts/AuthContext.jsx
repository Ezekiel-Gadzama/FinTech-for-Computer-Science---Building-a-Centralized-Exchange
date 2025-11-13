// Updated AuthContext.jsx
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
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');

    if (!token) {
      setLoading(false);
      setAuthChecked(true);
      return;
    }

    try {
      console.log('Checking authentication with token...');
      const response = await getCurrentUser();
      setUser(response.data.user);

      // Connect WebSocket after successful auth check
      console.log('Authentication successful, connecting WebSocket...');
      wsService.connect(token);

    } catch (error) {
      console.error('Authentication check failed:', error);

      // Don't automatically logout on network errors
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.log('Token invalid, clearing storage');
        localStorage.removeItem('token');
        setUser(null);
        wsService.disconnect();
      } else if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
        console.log('Network error - will retry later');
        // Keep the token for retry, but don't set user
      }
    } finally {
      setLoading(false);
      setAuthChecked(true);
    }
  };

  const loginUser = async (userData, token) => {
    localStorage.setItem('token', token);
    setUser(userData);

    // Connect WebSocket after login
    wsService.connect(token);
  };

  const logoutUser = () => {
    localStorage.removeItem('token');
    setUser(null);
    wsService.disconnect();
  };

  const refreshAuth = async () => {
    await checkAuth();
  };

  const value = {
    user,
    loading,
    authChecked,
    loginUser,
    logoutUser,
    refreshAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};