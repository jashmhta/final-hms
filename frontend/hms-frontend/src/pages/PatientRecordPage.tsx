import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

interface MedicalRecord {
  id: string;
  date: string;
  type: string;
  doctor: string;
  diagnosis: string;
  treatment: string;
  notes: string;
}

const PatientRecordPage: React.FC = () => {
  const [selectedRecord, setSelectedRecord] = useState<MedicalRecord | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  // Mock API call - replace with actual API integration
  const { data: records, isLoading } = useQuery({
    queryKey: ['patient-records'],
    queryFn: async () => {
      // Simulate API call
      return [
        {
          id: '1',
          date: '2024-09-15',
          type: 'Consultation',
          doctor: 'Dr. Smith',
          diagnosis: 'Hypertension',
          treatment: 'Prescribed medication',
          notes: 'Patient reports occasional headaches'
        },
        {
          id: '2',
          date: '2024-08-20',
          type: 'Lab Test',
          doctor: 'Dr. Johnson',
          diagnosis: 'Normal blood work',
          treatment: 'Continue current medication',
          notes: 'All parameters within normal range'
        },
        {
          id: '3',
          date: '2024-07-10',
          type: 'Follow-up',
          doctor: 'Dr. Smith',
          diagnosis: 'Improving condition',
          treatment: 'Adjust medication dosage',
          notes: 'Patient feeling better'
        }
      ];
    }
  });

  const filteredRecords = records?.filter(record => {
    const matchesSearch = record.diagnosis.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         record.doctor.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         record.type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || record.type.toLowerCase() === filterType.toLowerCase();
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
        <h1 className="text-3xl font-bold text-gray-900">Medical Records</h1>
        <button
          onClick={() => window.print()}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
        >
          Print Records
        </button>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search records..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="md:w-48">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <option value="all">All Types</option>
              <option value="consultation">Consultation</option>
              <option value="lab test">Lab Test</option>
              <option value="follow-up">Follow-up</option>
              <option value="surgery">Surgery</option>
            </select>
          </div>
        </div>
      </div>

      {/* Records List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Medical History</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {filteredRecords?.map((record) => (
            <div key={record.id} className="px-6 py-4 hover:bg-gray-50">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <h3 className="text-lg font-medium text-gray-900">{record.type}</h3>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                      {record.date}
                    </span>
                  </div>
                  <p className="text-gray-600 mt-1">Dr. {record.doctor}</p>
                  <p className="text-gray-800 mt-2"><strong>Diagnosis:</strong> {record.diagnosis}</p>
                  <p className="text-gray-600 mt-1"><strong>Treatment:</strong> {record.treatment}</p>
                  {record.notes && (
                    <p className="text-gray-600 mt-1"><strong>Notes:</strong> {record.notes}</p>
                  )}
                </div>
                <button
                  onClick={() => setSelectedRecord(record)}
                  className="text-blue-600 hover:text-blue-800 px-3 py-1 rounded border border-blue-600 ml-4"
                >
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Record Details Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Medical Record Details</h2>
              <button
                onClick={() => setSelectedRecord(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Date</label>
                  <p className="mt-1 text-gray-900">{selectedRecord.date}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Type</label>
                  <p className="mt-1 text-gray-900">{selectedRecord.type}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Doctor</label>
                  <p className="mt-1 text-gray-900">Dr. {selectedRecord.doctor}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Diagnosis</label>
                  <p className="mt-1 text-gray-900">{selectedRecord.diagnosis}</p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Treatment</label>
                <p className="mt-1 text-gray-900">{selectedRecord.treatment}</p>
              </div>
              {selectedRecord.notes && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Notes</label>
                  <p className="mt-1 text-gray-900">{selectedRecord.notes}</p>
                </div>
              )}
            </div>
            <div className="flex justify-end mt-6 space-x-2">
              <button
                onClick={() => window.print()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Print Record
              </button>
              <button
                onClick={() => setSelectedRecord(null)}
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

export default PatientRecordPage;