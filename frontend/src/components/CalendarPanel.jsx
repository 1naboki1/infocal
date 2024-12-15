import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Calendar as CalendarIcon, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';

export default function CalendarPanel({ warnings }) {
  const [selectedDate, setSelectedDate] = useState(new Date());

  // Group warnings by date
  const warningsByDate = warnings.reduce((acc, warning) => {
    const date = format(new Date(warning.start_time), 'yyyy-MM-dd');
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(warning);
    return acc;
  }, {});

  const getSeverityColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'bg-red-100 border-red-300 text-red-800';
      case 'medium':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'low':
        return 'bg-green-100 border-green-300 text-green-800';
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  const selectedDateWarnings = warningsByDate[format(selectedDate, 'yyyy-MM-dd')] || [];

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarIcon className="h-5 w-5" />
          Calendar Warnings
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-7 gap-1 text-center text-sm mb-2">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className="font-semibold">
              {day}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1">
          {Array.from({ length: 35 }).map((_, index) => {
            const date = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), index - selectedDate.getDay() + 1);
            const dateStr = format(date, 'yyyy-MM-dd');
            const hasWarnings = warningsByDate[dateStr]?.length > 0;

            return (
              <button
                key={index}
                onClick={() => setSelectedDate(date)}
                className={`
                  p-2 rounded-lg relative
                  ${format(date, 'MM') !== format(selectedDate, 'MM') ? 'text-gray-400' : ''}
                  ${format(date, 'yyyy-MM-dd') === format(selectedDate, 'yyyy-MM-dd') ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-100'}
                `}
              >
                {format(date, 'd')}
                {hasWarnings && (
                  <div className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></div>
                )}
              </button>
            );
          })}
        </div>

        <div className="mt-4 space-y-2">
          <h3 className="font-semibold">
            Warnings for {format(selectedDate, 'MMMM d, yyyy')}
          </h3>
          
          {selectedDateWarnings.length === 0 ? (
            <div className="text-center py-4 text-gray-500">
              No warnings for this date
            </div>
          ) : (
            selectedDateWarnings.map((warning) => (
              <div
                key={warning.id}
                className={`p-3 rounded-lg border ${getSeverityColor(warning.severity)}`}
              >
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold">
                      {warning.type} Warning
                    </div>
                    <div className="text-sm">
                      {warning.description}
                    </div>
                    <div className="text-xs mt-1">
                      {format(new Date(warning.start_time), 'HH:mm')} - 
                      {format(new Date(warning.end_time), 'HH:mm')}
                    </div>
                    <div className="text-xs">
                      Location: {warning.location.area}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {warnings.length > 0 && (
          <div className="mt-4 p-2 bg-gray-50 rounded-lg text-xs text-gray-500">
            {warnings.length} active warning{warnings.length !== 1 ? 's' : ''} in total
          </div>
        )}
      </CardContent>
    </Card>
  );
}
