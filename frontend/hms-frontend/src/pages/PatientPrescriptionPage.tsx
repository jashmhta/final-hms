import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

interface Prescription {
  id: string;
  medication: string;
  dosage: string;
  frequency: string;
  duration: string;
  doctor: string;
  date: string;
  status: 'active' | 'completed' | 'discontinued';
  instructions: string;
}

const PatientPrescriptionPage: React.FC = () => {
  const [selectedPrescription, setSelectedPrescription] = useState<Prescription | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  // Mock API call - replace with actual API integration
  const { data: prescriptions, isLoading } = useQuery({
    queryKey: ['patient-prescriptions'],
    queryFn: async () => {
      // Simulate API call
      return [
        {
          id: '1',
          medication: 'Lisinopril',
          dosage: '10mg',
          frequency: 'Once daily',
          duration: '30 days',
          doctor: 'Dr. Smith',
          date: '2024-09-15',
          status: 'active' as const,
          instructions: 'Take with food in the morning'
        },
        {
          id: '2',
          medication: 'Metformin',
          dosage: '500mg',
          frequency: 'Twice daily',
          duration: '60 days',
          doctor: 'Dr. Johnson',
          date: '2024-08-20',
          status: 'active' as const,
          instructions: 'Take with meals'
        },
        {
          id: '3',
          medication: 'Aspirin',
          dosage: '81mg',
          frequency: 'Once daily',
          duration: 'Completed',
          doctor: 'Dr. Smith',
          date: '2024-07-10',
          status: 'completed' as const,
          instructions: 'Take with water'
        }
      ];
    }
  });

  const filteredPrescriptions = prescriptions?.filter(prescription => {
    const matchesSearch = prescription.medication.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         prescription.doctor.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || prescription.status === filterStatus;
    return matchesSearch && matchesFilter;
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
        <h1 className="text-3xl font-bold text-gray-900">My Prescriptions</h1>
        <button
          onClick={() => window.print()}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
        >
          Print Prescriptions
        </button>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search medications or doctors..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="md:w-48">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="discontinued">Discontinued</option>
            </select>
          </div>
        </div>
      </div>

      {/* Prescriptions List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Current Prescriptions</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {filteredPrescriptions?.map((prescription) => (
            <div key={prescription.id} className="px-6 py-4 hover:bg-gray-50">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <h3 className="text-lg font-medium text-gray-900">{prescription.medication}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      prescription.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : prescription.status === 'completed'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {prescription.status}
                    </span>
                  </div>
                  <p className="text-gray-600 mt-1">
                    <strong>Dosage:</strong> {prescription.dosage} • <strong>Frequency:</strong> {prescription.frequency}
                  </p>
                  <p className="text-gray-600">
                    <strong>Duration:</strong> {prescription.duration} • <strong>Doctor:</strong> {prescription.doctor}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">Prescribed on: {prescription.date}</p>
                  {prescription.instructions && (
                    <p className="text-gray-600 mt-2"><strong>Instructions:</strong> {prescription.instructions}</p>
                  )}
                </div>
                <button
                  onClick={() => setSelectedPrescription(prescription)}
                  className="text-blue-600 hover:text-blue-800 px-3 py-1 rounded border border-blue-600 ml-4"
                >
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Prescription Details Modal */}
      {selectedPrescription && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Prescription Details</h2>
              <button
                onClick={() => setSelectedPrescription(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Medication</label>
                  <p className="mt-1 text-gray-900">{selectedPrescription.medication}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <span className={`inline-block mt-1 px-2 py-1 rounded-full text-xs font-medium ${
                    selectedPrescription.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : selectedPrescription.status === 'completed'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {selectedPrescription.status}
                  </span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Dosage</label>
                  <p className="mt-1 text-gray-900">{selectedPrescription.dosage}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Frequency</label>
                  <p className="mt-1 text-gray-900">{selectedPrescription.frequency}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Duration</label>
                  <p className="mt-1 text-gray-900">{selectedPrescription.duration}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Prescribed Date</label>
                  <p className="mt-1 text-gray-900">{selectedPrescription.date}</p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Prescribing Doctor</label>
                <p className="mt-1 text-gray-900">Dr. {selectedPrescription.doctor}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Instructions</label>
                <p className="mt-1 text-gray-900">{selectedPrescription.instructions}</p>
              </div>
            </div>
            <div className="flex justify-end mt-6 space-x-2">
              <button
                onClick={() => window.print()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Print Prescription
              </button>
              <button
                onClick={() => setSelectedPrescription(null)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
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

export default PatientPrescriptionPage;