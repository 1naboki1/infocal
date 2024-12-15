const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';

class ApiService {
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    };

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('token');
          localStorage.removeItem('user_email');
          window.location.reload();
          throw new Error('Session expired');
        }

        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || error.error || 'Request failed');
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return response.json();
      }
      return response.text();

    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Auth endpoints
  async initiateGoogleAuth() {
    return this.request('/auth/google', {
      method: 'POST'
    });
  }

  async checkAuthStatus() {
    return this.request('/auth/status');
  }

  // User endpoints
  async getUserProfile() {
    return this.request('/user/profile');
  }

  // Location endpoints
  async getLocations() {
    return this.request('/locations');
  }

  async addLocation(location) {
    return this.request('/locations', {
      method: 'POST',
      body: JSON.stringify({ location })
    });
  }

  async removeLocation(location) {
    return this.request('/locations', {
      method: 'DELETE',
      body: JSON.stringify({ location })
    });
  }

  async updateLocation(locationId, updates) {
    return this.request(`/locations/${locationId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  // Preference endpoints
  async getPreferences() {
    return this.request('/preferences');
  }

  async updatePreferences(preferences) {
    return this.request('/preferences', {
      method: 'PUT',
      body: JSON.stringify({ preferences })
    });
  }

  // Warning endpoints
  async getWarningHistory(limit = 50) {
    return this.request(`/warnings/history?limit=${limit}`);
  }

  async getActiveWarnings() {
    return this.request('/warnings/active');
  }

  async getWarningDetails(warningId) {
    return this.request(`/warnings/${warningId}`);
  }

  async markWarningRead(warningId) {
    return this.request(`/warnings/${warningId}/read`, {
      method: 'POST'
    });
  }

  // Calendar endpoints
  async getCalendarEvents(startDate, endDate) {
    const params = new URLSearchParams({
      start: startDate.toISOString(),
      end: endDate.toISOString()
    });
    return this.request(`/calendar/events?${params.toString()}`);
  }

  async createCalendarEvent(eventData) {
    return this.request('/calendar/events', {
      method: 'POST',
      body: JSON.stringify(eventData)
    });
  }

  async deleteCalendarEvent(eventId) {
    return this.request(`/calendar/events/${eventId}`, {
      method: 'DELETE'
    });
  }

  // Health check
  async checkHealth() {
    return this.request('/health');
  }

  // Error handling helper
  handleError(error) {
    console.error('API Error:', error);
    if (error.message.includes('Session expired')) {
      // Handle session expiry
      localStorage.clear();
      window.location.href = '/';
    }
    throw error;
  }
}

const api = new ApiService();
export default api;
