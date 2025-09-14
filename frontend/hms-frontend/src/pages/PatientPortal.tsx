import React from "react";
import { Link } from "react-router-dom";

const PatientPortal: React.FC = () => {
  return (
    <main className="container mx-auto px-4 py-8" role="main">
      <h1 className="text-3xl font-bold mb-8" id="patient-portal-title">
        Patient Portal
      </h1>
      <div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        aria-labelledby="patient-portal-title"
      >
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="appointments-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="appointments-heading">
            My Appointments
          </h2>
          <p className="text-gray-600 mb-4">
            View and manage your appointments
          </p>
          <Link
            to="/patient/appointments"
            className="text-blue-600 hover:text-blue-800"
            aria-label="View and manage your appointments"
          >
            View Appointments
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="records-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="records-heading">
            Medical Records
          </h2>
          <p className="text-gray-600 mb-4">Access your medical history</p>
          <Link
            to="/patient/records"
            className="text-blue-600 hover:text-blue-800"
            aria-label="Access your medical history"
          >
            View Records
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="prescriptions-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="prescriptions-heading">
            Prescriptions
          </h2>
          <p className="text-gray-600 mb-4">View your current prescriptions</p>
          <Link
            to="/patient/prescriptions"
            className="text-blue-600 hover:text-blue-800"
            aria-label="View your current prescriptions"
          >
            View Prescriptions
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="billing-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="billing-heading">
            Billing
          </h2>
          <p className="text-gray-600 mb-4">Check your bills and payments</p>
          <Link
            to="/patient/billing"
            className="text-blue-600 hover:text-blue-800"
            aria-label="Check your bills and payments"
          >
            View Billing
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="messages-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="messages-heading">
            Messages
          </h2>
          <p className="text-gray-600 mb-4">Communicate with your doctor</p>
          <Link
            to="/patient/messages"
            className="text-blue-600 hover:text-blue-800"
            aria-label="Communicate with your doctor"
          >
            View Messages
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="profile-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="profile-heading">
            Profile
          </h2>
          <p className="text-gray-600 mb-4">Update your personal information</p>
          <Link
            to="/patient/profile"
            className="text-blue-600 hover:text-blue-800"
            aria-label="Update your personal information"
          >
            Edit Profile
          </Link>
        </section>
      </div>
    </main>
  );
};

export default PatientPortal;
