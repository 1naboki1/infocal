export const WARNING_TYPES = {
    RAIN: {
      id: 'rain',
      label: 'Rain',
      description: 'Heavy rainfall and flood warnings',
      icon: '🌧️'
    },
    SNOW: {
      id: 'snow',
      label: 'Snow',
      description: 'Snowfall and blizzard warnings',
      icon: '❄️'
    },
    WIND: {
      id: 'wind',
      label: 'Wind',
      description: 'Strong winds and gale warnings',
      icon: '💨'
    },
    STORM: {
      id: 'storm',
      label: 'Storm',
      description: 'Thunderstorms and severe weather',
      icon: '⛈️'
    },
    HEAT: {
      id: 'heat',
      label: 'Heat',
      description: 'Extreme temperature and heat waves',
      icon: '🌡️'
    },
    FROST: {
      id: 'frost',
      label: 'Frost',
      description: 'Frost and freezing conditions',
      icon: '🥶'
    }
  };
  
  export const SEVERITY_LEVELS = {
    LOW: {
      value: 'low',
      label: 'Low',
      color: 'green',
      description: 'Minor weather conditions'
    },
    MEDIUM: {
      value: 'medium',
      label: 'Medium',
      color: 'yellow',
      description: 'Moderate weather conditions'
    },
    HIGH: {
      value: 'high',
      label: 'High',
      color: 'red',
      description: 'Severe weather conditions'
    },
    EXTREME: {
      value: 'extreme',
      label: 'Extreme',
      color: 'purple',
      description: 'Extremely dangerous conditions'
    }
  };
  
  export const API_ENDPOINTS = {
    AUTH: {
      LOGIN: '/auth/google',
      CALLBACK: '/oauth2callback',
      STATUS: '/auth/status'
    },
    LOCATIONS: '/locations',
    PREFERENCES: '/preferences',
    WARNINGS: {
      HISTORY: '/warnings/history'
    }
  };
