import React, { createContext, useContext, useState, useEffect } from 'react';
import api from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('token');
      const email = localStorage.getItem('user_email');
      
      console.log('Checking auth:', { token: !!token, email });

      if (token && email) {
        setIsAuthenticated(true);
        setUser({ email });
        console.log('User is authenticated:', { email });
      } else {
        setIsAuthenticated(false);
        setUser(null);
        console.log('User is not authenticated');
      }
    } catch (err) {
      console.error('Auth check failed:', err);
      setError('Authentication failed');
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthCallback = async (token, email) => {
    console.log('Handling auth callback:', { token: !!token, email });
    
    if (token && email) {
      localStorage.setItem('token', token);
      localStorage.setItem('user_email', email);
      setIsAuthenticated(true);
      setUser({ email });
      console.log('Auth state updated:', { isAuthenticated: true, email });
    }
  };

  const login = async () => {
    try {
      setError(null);
      const response = await api.initiateGoogleAuth();
      if (response.auth_url) {
        window.location.href = response.auth_url;
      }
    } catch (err) {
      console.error('Login failed:', err);
      setError('Failed to initialize login');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_email');
    setIsAuthenticated(false);
    setUser(null);
    console.log('User logged out');
  };

  const value = {
    isAuthenticated,
    user,
    loading,
    error,
    login,
    logout,
    checkAuth,
    handleAuthCallback
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
