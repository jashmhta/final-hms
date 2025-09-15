import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface PatientProfile {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  address: string;
  emergencyContact: string;
  emergencyPhone: string;
  insuranceProvider: string;
  insuranceId: string;
}

const PatientProfilePage: React.FC = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<PatientProfile | null>(null);
  const queryClient = useQueryClient();

  // Mock API call - replace with actual API integration
  const { data: profile, isLoading } = useQuery({
    queryKey: ['patient-profile'],
    queryFn: async () => {
      // Simulate API call
      return {
        id: '1',
        firstName: 'John',
        lastName: 'Doe',
        email: 'john.doe@example.com',
        phone: '(555) 123-4567',
        dateOfBirth: '1985-06-15',
        address: '123 Main St, Anytown, USA 12345',
        emergencyContact: 'Jane Doe',
        emergencyPhone: '(555) 987-6543',
        insuranceProvider: 'HealthPlus Insurance',
        insuranceId: 'HP123456789'
      };
    }
  });

  const updateProfileMutation = useMutation({
    mutationFn: async (updatedProfile: PatientProfile) => {
      // Simulate API call
      return { ...updatedProfile };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-profile'] });
      setIsEditing(false);
    }
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    );
  }

  const handleEdit = () => {
    setFormData(profile || null);
    setIsEditing(true);
  };

  const handleSave = () => {
    if (formData) {
      updateProfileMutation.mutate(formData);
    }
  };

  const handleCancel = () => {
    setFormData(null);
    setIsEditing(false);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
        {!isEditing && (
          <button
            onClick={handleEdit}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            Edit Profile
          </button>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Personal Information */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Personal Information</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData?.firstName || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, firstName: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.firstName}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData?.lastName || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, lastName: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.lastName}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              {isEditing ? (
                <input
                  type="email"
                  value={formData?.email || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, email: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              {isEditing ? (
                <input
                  type="tel"
                  value={formData?.phone || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, phone: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.phone}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
              {isEditing ? (
                <input
                  type="date"
                  value={formData?.dateOfBirth || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, dateOfBirth: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.dateOfBirth}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
              {isEditing ? (
                <textarea
                  value={formData?.address || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, address: e.target.value } : null)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.address}</p>
              )}
            </div>
          </div>

          {/* Emergency Contact & Insurance */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Emergency Contact</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact Name</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData?.emergencyContact || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, emergencyContact: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.emergencyContact}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact Phone</label>
              {isEditing ? (
                <input
                  type="tel"
                  value={formData?.emergencyPhone || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, emergencyPhone: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.emergencyPhone}</p>
              )}
            </div>

            <h2 className="text-xl font-semibold text-gray-900 mb-4 mt-8">Insurance Information</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Insurance Provider</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData?.insuranceProvider || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, insuranceProvider: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.insuranceProvider}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Insurance ID</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData?.insuranceId || ''}
                  onChange={(e) => setFormData(prev => prev ? { ...prev, insuranceId: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-gray-900">{profile?.insuranceId}</p>
              )}
            </div>
          </div>
        </div>

        {isEditing && (
          <div className="flex justify-end space-x-4 mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={handleCancel}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Save Changes
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientProfilePage;