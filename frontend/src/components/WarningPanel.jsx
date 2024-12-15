import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { AlertTriangle } from 'lucide-react';

export default function WarningPanel({ preferences = {}, onUpdatePreferences }) {
  const warningTypes = [
    { id: 'rain', label: 'Rain', description: 'Heavy rainfall and flood warnings' },
    { id: 'snow', label: 'Snow', description: 'Snowfall and blizzard warnings' },
    { id: 'wind', label: 'Wind', description: 'Strong winds and gale warnings' },
    { id: 'storm', label: 'Storm', description: 'Thunderstorms and severe weather' },
    { id: 'heat', label: 'Heat', description: 'Extreme temperature and heat waves' },
    { id: 'frost', label: 'Frost', description: 'Frost and freezing conditions' }
  ];

  const handleToggleWarning = (typeId) => {
    const newPreferences = {
      ...preferences,
      [typeId]: !preferences[typeId]
    };
    onUpdatePreferences(newPreferences);
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          Warning Types
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {warningTypes.map(({ id, label, description }) => (
            <div key={id} className="flex items-start space-x-3 p-2 rounded-lg hover:bg-gray-50">
              <Checkbox
                id={id}
                checked={preferences[id] ?? true}
                onChange={() => handleToggleWarning(id)}
                className="mt-1"
              />
              <div className="flex-1">
                <label
                  htmlFor={id}
                  className="text-sm font-medium cursor-pointer"
                >
                  {label}
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  {description}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-sm font-medium text-blue-800 mb-2">
            About Warning Notifications
          </h3>
          <p className="text-xs text-blue-600">
            Selected warnings will be automatically added to your Google Calendar. 
            You'll receive notifications based on your calendar settings.
          </p>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2">
          <button
            onClick={() => onUpdatePreferences(
              Object.fromEntries(warningTypes.map(type => [type.id, true]))
            )}
            className="px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            Enable All
          </button>
          <button
            onClick={() => onUpdatePreferences(
              Object.fromEntries(warningTypes.map(type => [type.id, false]))
            )}
            className="px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            Disable All
          </button>
        </div>

        {Object.values(preferences).every(v => !v) && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-100 rounded-lg">
            <p className="text-sm text-yellow-800">
              ⚠️ All warnings are currently disabled. You won't receive any notifications.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
