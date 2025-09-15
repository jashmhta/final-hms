import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface Message {
  id: string;
  sender: string;
  subject: string;
  content: string;
  timestamp: string;
  isRead: boolean;
  type: 'doctor' | 'system' | 'appointment';
}

const PatientMessagePage: React.FC = () => {
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [showComposeForm, setShowComposeForm] = useState(false);
  const [newMessage, setNewMessage] = useState({ subject: '', content: '' });
  const queryClient = useQueryClient();

  // Mock API calls - replace with actual API integration
  const { data: messages, isLoading } = useQuery({
    queryKey: ['patient-messages'],
    queryFn: async () => {
      // Simulate API call
      return [
        {
          id: '1',
          sender: 'Dr. Smith',
          subject: 'Follow-up on your recent visit',
          content: 'I wanted to check in on how you\'re feeling after your appointment. Please let me know if you have any concerns.',
          timestamp: '2024-09-15T10:30:00Z',
          isRead: false,
          type: 'doctor' as const
        },
        {
          id: '2',
          sender: 'System',
          subject: 'Appointment Reminder',
          content: 'You have an appointment scheduled for tomorrow at 2:00 PM with Dr. Johnson.',
          timestamp: '2024-09-14T14:00:00Z',
          isRead: true,
          type: 'appointment' as const
        },
        {
          id: '3',
          sender: 'Dr. Johnson',
          subject: 'Lab Results Available',
          content: 'Your recent lab results are now available in your patient portal. Please review them and contact us if you have any questions.',
          timestamp: '2024-09-10T09:15:00Z',
          isRead: true,
          type: 'doctor' as const
        }
      ];
    }
  });

  const markAsReadMutation = useMutation({
    mutationFn: async (messageId: string) => {
      // Simulate API call
      return { success: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-messages'] });
    }
  });

  const sendMessageMutation = useMutation({
    mutationFn: async (messageData: { subject: string; content: string }) => {
      // Simulate API call
      return {
        id: Date.now().toString(),
        sender: 'You',
        ...messageData,
        timestamp: new Date().toISOString(),
        isRead: true,
        type: 'doctor' as const
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-messages'] });
      setShowComposeForm(false);
      setNewMessage({ subject: '', content: '' });
    }
  });

  const unreadCount = messages?.filter(msg => !msg.isRead).length || 0;

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
        <h1 className="text-3xl font-bold text-gray-900">
          Messages {unreadCount > 0 && <span className="text-sm font-normal text-red-600">({unreadCount} unread)</span>}
        </h1>
        <button
          onClick={() => setShowComposeForm(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
        >
          Compose Message
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Messages List */}
        <div className="lg:col-span-1 bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Inbox</h2>
          </div>
          <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {messages?.map((message) => (
              <div
                key={message.id}
                onClick={() => {
                  setSelectedMessage(message);
                  if (!message.isRead) {
                    markAsReadMutation.mutate(message.id);
                  }
                }}
                className={`px-6 py-4 cursor-pointer hover:bg-gray-50 ${
                  !message.isRead ? 'bg-blue-50' : ''
                } ${selectedMessage?.id === message.id ? 'bg-green-50' : ''}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <p className="text-sm font-medium text-gray-900 truncate">{message.sender}</p>
                      {!message.isRead && (
                        <span className="inline-block w-2 h-2 bg-blue-600 rounded-full"></span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 truncate">{message.subject}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(message.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                    message.type === 'doctor'
                      ? 'bg-blue-100 text-blue-800'
                      : message.type === 'appointment'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {message.type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Message Content */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-md overflow-hidden">
          {selectedMessage ? (
            <div className="p-6">
              <div className="border-b border-gray-200 pb-4 mb-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">{selectedMessage.subject}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      From: {selectedMessage.sender} • {new Date(selectedMessage.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                    selectedMessage.type === 'doctor'
                      ? 'bg-blue-100 text-blue-800'
                      : selectedMessage.type === 'appointment'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {selectedMessage.type}
                  </span>
                </div>
              </div>
              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap">{selectedMessage.content}</p>
              </div>
              {selectedMessage.type === 'doctor' && (
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => setShowComposeForm(true)}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Reply
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64">
              <p className="text-gray-500">Select a message to view its content</p>
            </div>
          )}
        </div>
      </div>

      {/* Compose Message Modal */}
      {showComposeForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Compose Message</h2>
              <button
                onClick={() => setShowComposeForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <form onSubmit={(e) => {
              e.preventDefault();
              sendMessageMutation.mutate(newMessage);
            }}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">To</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500">
                  <option value="">Select Recipient</option>
                  <option value="doctor">My Doctor</option>
                  <option value="support">Support Team</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
                <input
                  type="text"
                  value={newMessage.subject}
                  onChange={(e) => setNewMessage({ ...newMessage, subject: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                <textarea
                  value={newMessage.content}
                  onChange={(e) => setNewMessage({ ...newMessage, content: e.target.value })}
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowComposeForm(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Send Message
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientMessagePage;