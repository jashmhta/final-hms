import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface Appointment {
  id: string;
  date: string;
  time: string;
  doctor: string;
  type: string;
  status: 'scheduled' | 'completed' | 'cancelled';
}

const PatientAppointmentPage: React.FC = () => {
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const queryClient = useQueryClient();

  // Mock API calls - replace with actual API integration
  const { data: appointments, isLoading } = useQuery({
    queryKey: ['patient-appointments'],
    queryFn: async () => {
      // Simulate API call
      return [
        {
          id: '1',
          date: '2024-09-20',
          time: '10:00 AM',
          doctor: 'Dr. Smith',
          type: 'General Checkup',
          status: 'scheduled' as const
        },
        {
          id: '2',
          date: '2024-09-15',
          time: '2:00 PM',
          doctor: 'Dr. Johnson',
          type: 'Follow-up',
          status: 'completed' as const
        }
      ];
    }
  });

  const bookAppointmentMutation = useMutation({
    mutationFn: async (appointmentData: Omit<Appointment, 'id' | 'status'>) => {
      // Simulate API call
      return { ...appointmentData, id: Date.now().toString(), status: 'scheduled' as const };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-appointments'] });
      setShowBookingForm(false);
    }
  });

  const cancelAppointmentMutation = useMutation({
    mutationFn: async (appointmentId: string) => {
      // Simulate API call
      return { success: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-appointments'] });
    }
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Appointments</h1>
        <button
          onClick={() => setShowBookingForm(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
        >
          Book New Appointment
        </button>
      </div>

      {/* Appointments List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Upcoming Appointments</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {appointments?.filter(apt => apt.status === 'scheduled').map((appointment) => (
            <div key={appointment.id} className="px-6 py-4 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-medium text-gray-900">{appointment.type}</h3>
                <p className="text-gray-600">{appointment.doctor}</p>
                <p className="text-sm text-gray-500">{appointment.date} at {appointment.time}</p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setSelectedAppointment(appointment)}
                  className="text-blue-600 hover:text-blue-800 px-3 py-1 rounded border border-blue-600"
                >
                  View Details
                </button>
                <button
                  onClick={() => cancelAppointmentMutation.mutate(appointment.id)}
                  className="text-red-600 hover:text-red-800 px-3 py-1 rounded border border-red-600"
                >
                  Cancel
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Appointment History */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden mt-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Appointment History</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {appointments?.filter(apt => apt.status !== 'scheduled').map((appointment) => (
            <div key={appointment.id} className="px-6 py-4">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{appointment.type}</h3>
                  <p className="text-gray-600">{appointment.doctor}</p>
                  <p className="text-sm text-gray-500">{appointment.date} at {appointment.time}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  appointment.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {appointment.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Booking Form Modal */}
      {showBookingForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Book New Appointment</h2>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.target as HTMLFormElement);
              bookAppointmentMutation.mutate({
                date: formData.get('date') as string,
                time: formData.get('time') as string,
                doctor: formData.get('doctor') as string,
                type: formData.get('type') as string,
              });
            }}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                <input
                  type="date"
                  name="date"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Time</label>
                <input
                  type="time"
                  name="time"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Doctor</label>
                <select
                  name="doctor"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="">Select Doctor</option>
                  <option value="Dr. Smith">Dr. Smith</option>
                  <option value="Dr. Johnson">Dr. Johnson</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Appointment Type</label>
                <select
                  name="type"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="">Select Type</option>
                  <option value="General Checkup">General Checkup</option>
                  <option value="Follow-up">Follow-up</option>
                  <option value="Consultation">Consultation</option>
                </select>
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowBookingForm(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Book Appointment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Appointment Details Modal */}
      {selectedAppointment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Appointment Details</h2>
            <div className="space-y-2">
              <p><strong>Type:</strong> {selectedAppointment.type}</p>
              <p><strong>Doctor:</strong> {selectedAppointment.doctor}</p>
              <p><strong>Date:</strong> {selectedAppointment.date}</p>
              <p><strong>Time:</strong> {selectedAppointment.time}</p>
              <p><strong>Status:</strong> {selectedAppointment.status}</p>
            </div>
            <div className="flex justify-end mt-4">
              <button
                onClick={() => setSelectedAppointment(null)}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientAppointmentPage;