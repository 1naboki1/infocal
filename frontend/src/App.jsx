import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import LocationPanel from './components/LocationPanel';
import CalendarPanel from './components/CalendarPanel';
import WarningPanel from './components/WarningPanel';
import { useAuth } from './services/auth';
import api from './services/api';

export default function App() {
  const { isAuthenticated, login, handleAuthCallback, error: authError } = useAuth();
  const [locations, setLocations] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [preferences, setPreferences] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check URL parameters for auth callback
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const email = params.get('email');

    if (token && email) {
      console.log('Found auth parameters:', { token: !!token, email });
      handleAuthCallback(token, email);
      // Clean up URL
      window.history.replaceState({}, document.title, '/');
    }
  }, [handleAuthCallback]);

  useEffect(() => {
    console.log('Authentication state changed:', isAuthenticated);
    if (isAuthenticated) {
      fetchUserData();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const fetchUserData = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching user data...');

      const [locationsRes, preferencesRes, warningsRes] = await Promise.all([
        api.getLocations(),
        api.getPreferences(),
        api.getWarningHistory()
      ]);

      console.log('Fetched data:', { 
        locations: locationsRes.locations, 
        preferences: preferencesRes.preferences,
        warnings: warningsRes.history
      });

      setLocations(locationsRes.locations || []);
      setPreferences(preferencesRes.preferences || {});
      setWarnings(warningsRes.history || []);
    } catch (err) {
      console.error('Failed to fetch user data:', err);
      setError('Failed to fetch user data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddLocation = async (location) => {
    try {
      setError(null);
      const response = await api.addLocation(location);
      console.log('Added location:', response.location);
      setLocations([...locations, response.location]);
    } catch (err) {
      console.error('Failed to add location:', err);
      setError('Failed to add location');
    }
  };

  const handleRemoveLocation = async (location) => {
    try {
      setError(null);
      await api.removeLocation(location);
      console.log('Removed location:', location);
      setLocations(locations.filter(loc => loc.name !== location.name));
    } catch (err) {
      console.error('Failed to remove location:', err);
      setError('Failed to remove location');
    }
  };

  const handleUpdatePreferences = async (newPreferences) => {
    try {
      setError(null);
      await api.updatePreferences(newPreferences);
      console.log('Updated preferences:', newPreferences);
      setPreferences(newPreferences);
    } catch (err) {
      console.error('Failed to update preferences:', err);
      setError('Failed to update preferences');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      {(error || authError) && (
        <Alert variant="destructive" className="mb-4 max-w-7xl mx-auto">
          <AlertDescription>{error || authError}</AlertDescription>
        </Alert>
      )}

      {!isAuthenticated ? (
        <div className="max-w-md mx-auto mt-10">
          <Card className="p-6">
            <h1 className="text-2xl font-bold text-center mb-6">Welcome to InfoCal</h1>
            <p className="text-gray-600 text-center mb-8">
              Get weather warnings directly in your Google Calendar.
              Please sign in with your Google account to continue.
            </p>
            <button
              onClick={login}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
            >
              <svg 
                className="w-5 h-5" 
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z"/>
              </svg>
              Sign in with Google
            </button>
          </Card>
        </div>
      ) : (
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          <LocationPanel
            locations={locations}
            onAddLocation={handleAddLocation}
            onRemoveLocation={handleRemoveLocation}
          />
          <CalendarPanel warnings={warnings} />
          <WarningPanel
            preferences={preferences}
            onUpdatePreferences={handleUpdatePreferences}
          />
        </div>
      )}
    </div>
  );
}
