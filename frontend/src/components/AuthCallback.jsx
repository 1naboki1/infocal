import React, { useEffect } from 'react';
import { useAuth } from '../services/auth';

export default function AuthCallback() {
  const { handleAuthCallback } = useAuth();

  useEffect(() => {
    const processCallback = () => {
      try {
        const params = new URLSearchParams(window.location.search);
        const token = params.get('token');
        const email = params.get('email');
        const error = params.get('error');

        if (error) {
          console.error('Auth error:', error);
          window.location.href = '/';
          return;
        }
        
        if (token && email) {
          handleAuthCallback(token, email);
          window.location.href = '/';
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        window.location.href = '/?error=auth_failed';
      }
    };

    processCallback();
  }, [handleAuthCallback]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>
  );
}
