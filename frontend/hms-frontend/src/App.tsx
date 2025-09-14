const ERPPage = lazy(() => import("./pages/ERPPage"));
const AccountingPage = lazy(() => import("./pages/AccountingPage"));
import React, { Suspense, lazy, type ReactNode } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./hooks/useAuth";

const LoginPage = lazy(() => import("./pages/LoginPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const PatientsPage = lazy(() => import("./pages/PatientsPage"));
const AppointmentsPage = lazy(() => import("./pages/AppointmentsPage"));
const BedsPage = lazy(() => import("./pages/BedManagementPage"));
const TriagePage = lazy(() => import("./pages/TriagePage"));
const NotificationsPage = lazy(() => import("./pages/NotificationsPage"));
const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage"));
const RadiologyPage = lazy(() => import("./pages/RadiologyPage"));
const FeedbackPage = lazy(() => import("./pages/FeedbackPage"));
const ConsentPage = lazy(() => import("./pages/ConsentPage"));
const AuditPage = lazy(() => import("./pages/AuditPage"));
const ERAlertsPage = lazy(() => import("./pages/ERAlertsPage"));
const OTSchedulingPage = lazy(() => import("./pages/OTSchedulingPage"));
const SuperAdminPage = lazy(() => import("./pages/SuperAdminPage"));
const PatientPortal = lazy(() => import("./pages/PatientPortal"));
const DoctorPortal = lazy(() => import("./pages/DoctorPortal"));

const queryClient = new QueryClient();

function PrivateRoute({ children }: { children: ReactNode }) {
  const token = localStorage.getItem("accessToken");
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AdminShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const isAdmin =
    user?.role === "SUPER_ADMIN" || user?.role === "HOSPITAL_ADMIN";
  const isSuper = user?.role === "SUPER_ADMIN";
  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-blue-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-bold">
                HMS Admin
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/" className="hover:bg-blue-700 px-3 py-2 rounded">
                Dashboard
              </Link>
              <Link
                to="/patients"
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                Patients
              </Link>
              <Link
                to="/appointments"
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                Appointments
              </Link>
              <Link to="/beds" className="hover:bg-blue-700 px-3 py-2 rounded">
                Beds
              </Link>
              <Link
                to="/triage"
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                Triage
              </Link>
              <Link
                to="/analytics"
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                Analytics
              </Link>
              <Link
                to="/radiology"
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                Radiology
              </Link>
              <Link
                to="/feedback"
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                Feedback
              </Link>
              <Link
                to="/consent"
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                Consent
              </Link>
              <Link
                to="/er-alerts"
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                ER Alerts
              </Link>
              <Link
                to="/ot-scheduling"
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                OT
              </Link>
              {isAdmin && (
                <Link
                  to="/audit"
                  className="hover:bg-blue-700 px-3 py-2 rounded"
                >
                  Audit
                </Link>
              )}
              {isAdmin && (
                <Link
                  to="/notifications"
                  className="hover:bg-blue-700 px-3 py-2 rounded"
                >
                  Notifications
                </Link>
              )}
              {isSuper && (
                <Link
                  to="/superadmin"
                  className="hover:bg-blue-700 px-3 py-2 rounded"
                >
                  Superadmin
                </Link>
              )}
              <button
                onClick={logout}
                className="hover:bg-blue-700 px-3 py-2 rounded"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}

function PatientShell({ children }: { children: ReactNode }) {
  const { logout } = useAuth();
  return (
    <div className="min-h-screen bg-green-50">
      <nav className="bg-green-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/patient" className="text-xl font-bold">
                Patient Portal
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/patient" className="hover:bg-green-700 px-3 py-2 rounded">
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="hover:bg-green-700 px-3 py-2 rounded"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}

function DoctorShell({ children }: { children: ReactNode }) {
  const { logout } = useAuth();
  return (
    <div className="min-h-screen bg-purple-50">
      <nav className="bg-purple-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/doctor" className="text-xl font-bold">
                Doctor Portal
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/doctor" className="hover:bg-purple-700 px-3 py-2 rounded">
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="hover:bg-purple-700 px-3 py-2 rounded"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Suspense
            fallback={
              <div className="flex justify-center items-center h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            }
          >
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <DashboardPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/patients"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <PatientsPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/appointments"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <AppointmentsPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/beds"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <BedsPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/triage"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <TriagePage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/analytics"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <AnalyticsPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/radiology"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <RadiologyPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/feedback"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <FeedbackPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/consent"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <ConsentPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/er-alerts"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <ERAlertsPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/ot-scheduling"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <OTSchedulingPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/audit"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <AuditPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/erp"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <ERPPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/accounting"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <AccountingPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/notifications"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <NotificationsPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/superadmin"
                element={
                  <PrivateRoute>
                    <AdminShell>
                      <SuperAdminPage />
                    </AdminShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/patient"
                element={
                  <PrivateRoute>
                    <PatientShell>
                      <PatientPortal />
                    </PatientShell>
                  </PrivateRoute>
                }
              />
              <Route
                path="/doctor"
                element={
                  <PrivateRoute>
                    <DoctorShell>
                      <DoctorPortal />
                    </DoctorShell>
                  </PrivateRoute>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </QueryClientProvider>
    </AuthProvider>
  );
}

export default App;
