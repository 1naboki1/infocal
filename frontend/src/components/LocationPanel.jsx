import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Map, X } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';

// Helper component to update map view
function MapUpdater({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center && center.length === 2) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);
  return null;
}

export default function LocationPanel({ locations = [], onAddLocation, onRemoveLocation }) {
  const [newLocation, setNewLocation] = useState('');
  const [error, setError] = useState(null);
  const [isAdding, setIsAdding] = useState(false);
  const [mapCenter, setMapCenter] = useState([48.2082, 16.3738]); // Vienna default
  const [mapZoom, setMapZoom] = useState(12);

  // Update map center when locations change
  useEffect(() => {
    if (locations.length > 0) {
      const lastLocation = locations[locations.length - 1];
      if (lastLocation.lat && lastLocation.lon) {
        setMapCenter([lastLocation.lat, lastLocation.lon]);
      }
    }
  }, [locations]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newLocation.trim()) return;

    try {
      setIsAdding(true);
      setError(null);
      await onAddLocation(newLocation.trim());
      setNewLocation('');
    } catch (err) {
      console.error('Failed to add location:', err);
      setError(err.message || 'Failed to add location');
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveLocation = async (location) => {
    try {
      await onRemoveLocation(location);
      // If we removed the last location, center map on previous location
      if (locations.length > 1) {
        const newLastLocation = locations[locations.length - 2];
        setMapCenter([newLastLocation.lat, newLastLocation.lon]);
      } else {
        // If no locations left, reset to Vienna
        setMapCenter([48.2082, 16.3738]);
      }
    } catch (err) {
      setError('Failed to remove location');
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Map className="h-5 w-5" />
          Locations
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
          <Input
            value={newLocation}
            onChange={(e) => setNewLocation(e.target.value)}
            placeholder="Add new location..."
            disabled={isAdding}
            className="flex-1"
          />
          <Button type="submit" disabled={isAdding}>
            {isAdding ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              'Add'
            )}
          </Button>
        </form>

        {locations.length > 0 && (
          <>
            <div className="mb-4 h-48">
              <MapContainer
                center={mapCenter}
                zoom={mapZoom}
                className="h-full w-full rounded-lg"
                scrollWheelZoom={false}
              >
                <MapUpdater center={mapCenter} zoom={mapZoom} />
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {locations.map((location) => (
                  location.lat && location.lon && (
                    <Marker
                      key={`${location.name}-${location.lat}-${location.lon}`}
                      position={[location.lat, location.lon]}
                    >
                      <Popup>
                        <div className="font-medium">{location.name}</div>
                        {location.address && (
                          <div className="text-sm text-gray-500 mt-1">{location.address}</div>
                        )}
                      </Popup>
                    </Marker>
                  )
                ))}
              </MapContainer>
            </div>

            <div className="mt-4 space-y-2">
              {locations.map((location) => (
                <div
                  key={`location-list-${location.name}-${location.lat}-${location.lon}`}
                  className="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{location.name}</div>
                    {location.address && (
                      <div className="text-sm text-gray-500 truncate">{location.address}</div>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveLocation(location)}
                    className="ml-2 text-red-500 hover:text-red-700 hover:bg-red-50 shrink-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </>
        )}

        {locations.length === 0 && (
          <div className="text-center text-gray-500 mt-4 p-8 bg-gray-50 rounded-lg">
            <Map className="h-12 w-12 mx-auto mb-3 text-gray-400" />
            <p className="font-medium">No locations added</p>
            <p className="text-sm mt-1">Add your first location using the input above</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
