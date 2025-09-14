import React from "react";
import { Link } from "react-router-dom";

const DoctorPortal: React.FC = () => {
  return (
    <main className="container mx-auto px-4 py-8" role="main">
      <h1 className="text-3xl font-bold mb-8" id="doctor-portal-title">
        Doctor Portal
      </h1>
      <div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        aria-labelledby="doctor-portal-title"
      >
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="patients-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="patients-heading">
            My Patients
          </h2>
          <p className="text-gray-600 mb-4">View and manage your patients</p>
          <Link
            to="/doctor/patients"
            className="text-blue-600 hover:text-blue-800"
            aria-label="View and manage your patients"
          >
            View Patients
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="appointments-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="appointments-heading">
            Appointments
          </h2>
          <p className="text-gray-600 mb-4">Schedule and manage appointments</p>
          <Link
            to="/doctor/appointments"
            className="text-blue-600 hover:text-blue-800"
            aria-label="Schedule and manage appointments"
          >
            Manage Appointments
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="prescriptions-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="prescriptions-heading">
            Prescriptions
          </h2>
          <p className="text-gray-600 mb-4">Prescribe medications</p>
          <Link
            to="/doctor/prescriptions"
            className="text-blue-600 hover:text-blue-800"
            aria-label="Prescribe medications"
          >
            Manage Prescriptions
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="lab-results-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="lab-results-heading">
            Lab Results
          </h2>
          <p className="text-gray-600 mb-4">Review lab and test results</p>
          <Link
            to="/doctor/lab-results"
            className="text-blue-600 hover:text-blue-800"
            aria-label="Review lab and test results"
          >
            View Results
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="messages-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="messages-heading">
            Messages
          </h2>
          <p className="text-gray-600 mb-4">Communicate with patients</p>
          <Link
            to="/doctor/messages"
            className="text-blue-600 hover:text-blue-800"
            aria-label="Communicate with patients"
          >
            View Messages
          </Link>
        </section>
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="reports-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="reports-heading">
            Reports
          </h2>
          <p className="text-gray-600 mb-4">Generate and view reports</p>
          <Link
            to="/doctor/reports"
            className="text-blue-600 hover:text-blue-800"
            aria-label="Generate and view reports"
          >
            View Reports
          </Link>
        </section>
      </div>
    </main>
  );
};

export default DoctorPortal;
