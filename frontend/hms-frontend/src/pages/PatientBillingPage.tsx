import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

interface Bill {
  id: string;
  date: string;
  description: string;
  amount: number;
  status: 'paid' | 'pending' | 'overdue';
  dueDate: string;
  service: string;
}

interface Payment {
  id: string;
  date: string;
  amount: number;
  method: string;
  billId: string;
  status: 'completed' | 'failed' | 'pending';
}

const PatientBillingPage: React.FC = () => {
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('credit_card');

  // Mock API calls - replace with actual API integration
  const { data: bills, isLoading: billsLoading } = useQuery({
    queryKey: ['patient-bills'],
    queryFn: async () => {
      // Simulate API call
      return [
        {
          id: '1',
          date: '2024-09-15',
          description: 'Consultation Fee',
          amount: 150.00,
          status: 'paid' as const,
          dueDate: '2024-09-20',
          service: 'General Consultation'
        },
        {
          id: '2',
          date: '2024-09-10',
          description: 'Lab Tests',
          amount: 250.00,
          status: 'pending' as const,
          dueDate: '2024-09-25',
          service: 'Blood Work & Urinalysis'
        },
        {
          id: '3',
          date: '2024-08-20',
          description: 'X-Ray',
          amount: 300.00,
          status: 'overdue' as const,
          dueDate: '2024-09-05',
          service: 'Chest X-Ray'
        }
      ];
    }
  });

  const { data: payments, isLoading: paymentsLoading } = useQuery({
    queryKey: ['patient-payments'],
    queryFn: async () => {
      // Simulate API call
      return [
        {
          id: '1',
          date: '2024-09-16',
          amount: 150.00,
          method: 'Credit Card',
          billId: '1',
          status: 'completed' as const
        },
        {
          id: '2',
          date: '2024-08-21',
          amount: 300.00,
          method: 'Insurance',
          billId: '3',
          status: 'completed' as const
        }
      ];
    }
  });

  const totalOutstanding = bills?.filter(bill => bill.status !== 'paid').reduce((sum, bill) => sum + bill.amount, 0) || 0;
  const totalPaid = bills?.filter(bill => bill.status === 'paid').reduce((sum, bill) => sum + bill.amount, 0) || 0;

  if (billsLoading || paymentsLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Billing & Payments</h1>
        <button
          onClick={() => setShowPaymentForm(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
        >
          Make Payment
        </button>
      </div>

      {/* Billing Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Outstanding</h3>
          <p className="text-2xl font-bold text-red-600">${totalOutstanding.toFixed(2)}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Paid</h3>
          <p className="text-2xl font-bold text-green-600">${totalPaid.toFixed(2)}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Next Due Date</h3>
          <p className="text-lg text-gray-600">
            {bills?.filter(bill => bill.status === 'pending').sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime())[0]?.dueDate || 'No pending bills'}
          </p>
        </div>
      </div>

      {/* Bills List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Current Bills</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {bills?.map((bill) => (
            <div key={bill.id} className="px-6 py-4 hover:bg-gray-50">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <h3 className="text-lg font-medium text-gray-900">{bill.description}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      bill.status === 'paid'
                        ? 'bg-green-100 text-green-800'
                        : bill.status === 'pending'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {bill.status}
                    </span>
                  </div>
                  <p className="text-gray-600 mt-1">{bill.service}</p>
                  <p className="text-sm text-gray-500">Date: {bill.date} • Due: {bill.dueDate}</p>
                  <p className="text-lg font-semibold text-gray-900 mt-2">${bill.amount.toFixed(2)}</p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedBill(bill)}
                    className="text-blue-600 hover:text-blue-800 px-3 py-1 rounded border border-blue-600"
                  >
                    View Details
                  </button>
                  {bill.status !== 'paid' && (
                    <button
                      onClick={() => setShowPaymentForm(true)}
                      className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700"
                    >
                      Pay Now
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Payment History */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Payment History</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {payments?.map((payment) => (
            <div key={payment.id} className="px-6 py-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-lg font-medium text-gray-900">${payment.amount.toFixed(2)}</p>
                  <p className="text-gray-600">{payment.method}</p>
                  <p className="text-sm text-gray-500">Date: {payment.date}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  payment.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : payment.status === 'pending'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {payment.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bill Details Modal */}
      {selectedBill && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Bill Details</h2>
              <button
                onClick={() => setSelectedBill(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Service</label>
                <p className="mt-1 text-gray-900">{selectedBill.service}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <p className="mt-1 text-gray-900">{selectedBill.description}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Date</label>
                <p className="mt-1 text-gray-900">{selectedBill.date}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Due Date</label>
                <p className="mt-1 text-gray-900">{selectedBill.dueDate}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Amount</label>
                <p className="mt-1 text-xl font-bold text-gray-900">${selectedBill.amount.toFixed(2)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Status</label>
                <span className={`inline-block mt-1 px-2 py-1 rounded-full text-xs font-medium ${
                  selectedBill.status === 'paid'
                    ? 'bg-green-100 text-green-800'
                    : selectedBill.status === 'pending'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {selectedBill.status}
                </span>
              </div>
            </div>
            <div className="flex justify-end mt-6 space-x-2">
              <button
                onClick={() => window.print()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Print Bill
              </button>
              <button
                onClick={() => setSelectedBill(null)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payment Form Modal */}
      {showPaymentForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Make Payment</h2>
              <button
                onClick={() => setShowPaymentForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <form onSubmit={(e) => {
              e.preventDefault();
              // Handle payment submission
              alert('Payment processed successfully!');
              setShowPaymentForm(false);
            }}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="credit_card">Credit Card</option>
                  <option value="debit_card">Debit Card</option>
                  <option value="bank_transfer">Bank Transfer</option>
                  <option value="insurance">Insurance</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="Enter amount"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>
              {paymentMethod === 'credit_card' || paymentMethod === 'debit_card' ? (
                <>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Card Number</label>
                    <input
                      type="text"
                      placeholder="1234 5678 9012 3456"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
                      <input
                        type="text"
                        placeholder="MM/YY"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">CVV</label>
                      <input
                        type="text"
                        placeholder="123"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                        required
                      />
                    </div>
                  </div>
                </>
              ) : null}
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowPaymentForm(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Process Payment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientBillingPage;