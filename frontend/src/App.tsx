import { useState } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { DashboardModule } from './components/modules/DashboardModule';
import { PatientsModule } from './components/modules/PatientsModule';
import { DoctorsModule } from './components/modules/DoctorsModule';
import { DepartmentsModule } from './components/modules/DepartmentsModule';
import { AppointmentsModule } from './components/modules/AppointmentsModule';
import { BillingModule } from './components/modules/BillingModule';
import { ERPModule } from './components/modules/ERPModule';

// Placeholder components for new modules
const PlaceholderModule = ({ title, description }: { title: string; description: string }) => (
  <div className="space-y-6">
    <div>
      <h1 className="text-2xl text-gray-900 dark:text-gray-100">{title}</h1>
      <p className="text-gray-600 dark:text-gray-400">{description}</p>
    </div>
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
      <div className="mx-auto w-24 h-24 bg-teal-50 dark:bg-teal-900 rounded-full flex items-center justify-center mb-4">
        <div className="w-12 h-12 bg-teal-100 dark:bg-teal-800 rounded-full flex items-center justify-center">
          <div className="w-6 h-6 bg-teal-500 rounded-full"></div>
        </div>
      </div>
      <h3 className="text-lg text-gray-900 dark:text-gray-100 mb-2">Module Under Development</h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">This module is currently being developed and will be available soon.</p>
      <p className="text-sm text-gray-500 dark:text-gray-400">Expected features: {description}</p>
    </div>
  </div>
);

export default function App() {
  const [activeModule, setActiveModule] = useState('dashboard');

  const renderActiveModule = () => {
    switch (activeModule) {
      case 'dashboard':
        return <DashboardModule />;
      case 'patients':
        return <PatientsModule />;
      case 'appointments':
        return <AppointmentsModule />;
      case 'doctors':
        return <DoctorsModule />;
      case 'opd':
        return <PlaceholderModule
          title="Outpatient Department (OPD)"
          description="OPD visits logging, consultation notes, prescriptions, and patient flow management"
        />;
      case 'ipd':
        return <PlaceholderModule
          title="Inpatient Department (IPD)"
          description="Bed allocation, ward management, admission notes, progress notes, and discharge summaries"
        />;
      case 'emergency':
        return <div className="space-y-6">
          <div>
            <h1 className="text-2xl text-gray-900 dark:text-gray-100">Emergency Department</h1>
            <p className="text-gray-600 dark:text-gray-400">Critical patient care, triage management, and emergency protocols</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-600">Critical Patients</p>
                  <p className="text-2xl text-red-700">3</p>
                </div>
                <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
                </div>
              </div>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-600">High Priority</p>
                  <p className="text-2xl text-orange-700">7</p>
                </div>
                <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-orange-500 rounded-full"></div>
                </div>
              </div>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-yellow-600">Medium Priority</p>
                  <p className="text-2xl text-yellow-700">12</p>
                </div>
                <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-yellow-500 rounded-full"></div>
                </div>
              </div>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-600">Low Priority</p>
                  <p className="text-2xl text-green-700">18</p>
                </div>
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                </div>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg text-gray-900 dark:text-gray-100 mb-4">Emergency Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-3">
                <h4 className="text-sm text-gray-700 dark:text-gray-300">Triage Management</h4>
                <ul className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                  <li>• Priority-based patient classification</li>
                  <li>• Real-time bed availability</li>
                  <li>• Automated alert system</li>
                  <li>• Quick registration process</li>
                </ul>
              </div>
              <div className="space-y-3">
                <h4 className="text-sm text-gray-700 dark:text-gray-300">Critical Alerts</h4>
                <ul className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                  <li>• Code blue notifications</li>
                  <li>• Staff instant messaging</li>
                  <li>• Equipment status tracking</li>
                  <li>• Emergency contacts</li>
                </ul>
              </div>
              <div className="space-y-3">
                <h4 className="text-sm text-gray-700 dark:text-gray-300">Documentation</h4>
                <ul className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                  <li>• Emergency admission forms</li>
                  <li>• Treatment protocols</li>
                  <li>• Discharge summaries</li>
                  <li>• Legal compliance tracking</li>
                </ul>
              </div>
            </div>
          </div>
        </div>;
      case 'departments':
        return <DepartmentsModule />;
      case 'pharmacy':
        return <div className="space-y-6">
          <div>
            <h1 className="text-2xl text-gray-900 dark:text-gray-100">Pharmacy & Inventory</h1>
            <p className="text-gray-600 dark:text-gray-400">Manage medicine stock, issues, and purchase orders</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
            <div className="mx-auto w-24 h-24 bg-teal-50 dark:bg-teal-900 rounded-full flex items-center justify-center mb-4">
              <div className="w-12 h-12 bg-teal-100 dark:bg-teal-800 rounded-full flex items-center justify-center">
                <div className="w-6 h-6 bg-teal-500 rounded-full"></div>
              </div>
            </div>
            <h3 className="text-lg text-gray-900 dark:text-gray-100 mb-2">Pharmacy Module</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">Complete pharmacy management system with inventory tracking, stock alerts, and medicine dispensing.</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="text-sm text-gray-700 dark:text-gray-300 mb-2">Inventory Management</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">Track medicine stock levels and expiry dates</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="text-sm text-gray-700 dark:text-gray-300 mb-2">Issue to Patients</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">Dispense medicines with prescription tracking</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="text-sm text-gray-700 dark:text-gray-300 mb-2">Purchase Orders</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">Manage supplier orders and deliveries</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="text-sm text-gray-700 dark:text-gray-300 mb-2">Expiry Alerts</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">Get notified about expiring medicines</p>
              </div>
            </div>
          </div>
        </div>;
      case 'laboratory':
        return <div className="space-y-6">
          <div>
            <h1 className="text-2xl text-gray-900 dark:text-gray-100">Laboratory & Diagnostics</h1>
            <p className="text-gray-600 dark:text-gray-400">Comprehensive lab management with test tracking and result processing</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-600">Tests Today</p>
                  <p className="text-2xl text-blue-700">156</p>
                </div>
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                </div>
              </div>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-600">Completed</p>
                  <p className="text-2xl text-green-700">132</p>
                </div>
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                </div>
              </div>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-600">Pending</p>
                  <p className="text-2xl text-orange-700">24</p>
                </div>
                <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-orange-500 rounded-full"></div>
                </div>
              </div>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-600">Critical Results</p>
                  <p className="text-2xl text-purple-700">3</p>
                </div>
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-purple-500 rounded-full animate-pulse"></div>
                </div>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg text-gray-900 dark:text-gray-100 mb-4">Laboratory Management Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h4 className="text-sm text-gray-700 dark:text-gray-300">Test Categories</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-600">Blood Tests</span>
                    <span className="text-xs text-gray-500">45 tests</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-600">Urine Analysis</span>
                    <span className="text-xs text-gray-500">23 tests</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-600">Microbiology</span>
                    <span className="text-xs text-gray-500">18 tests</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-600">Biochemistry</span>
                    <span className="text-xs text-gray-500">35 tests</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-600">Pathology</span>
                    <span className="text-xs text-gray-500">12 tests</span>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <h4 className="text-sm text-gray-700">Key Features</h4>
                <ul className="text-xs text-gray-500 space-y-2">
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-2"></div>
                    Sample collection tracking with barcode scanning
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-2"></div>
                    Automated result validation and verification
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-2"></div>
                    Critical value alerts and notifications
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-2"></div>
                    Digital report generation and printing
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-2"></div>
                    Quality control and calibration tracking
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-teal-500 rounded-full mr-2"></div>
                    Integration with LIS (Laboratory Information System)
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>;
      case 'radiology':
        return <PlaceholderModule
          title="Radiology & Imaging"
          description="Scan requests (X-ray, CT, MRI, Ultrasound), image upload/viewer, and radiologist reports"
        />;
      case 'billing':
        return <BillingModule />;
      case 'erp':
        return <ERPModule />;
      case 'reports':
        return <PlaceholderModule
          title="Reports & Analytics"
          description="Patient reports, revenue analysis, inventory usage, doctor performance, and custom report builder"
        />;
      case 'users':
        return <PlaceholderModule
          title="User Management & Security"
          description="Role management (Admin, Doctor, Nurse, Receptionist), access control, and audit trails"
        />;
      case 'notifications':
        return <PlaceholderModule
          title="Notifications & Communication"
          description="SMS/Email integration, appointment reminders, billing alerts, and internal messaging"
        />;
      case 'settings':
        return <PlaceholderModule
          title="Settings & Configuration"
          description="Hospital info & branding, SMTP/SMS API config, backup & restore, and system settings"
        />;
      default:
        return <DashboardModule />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header onModuleChange={setActiveModule} />
      <div className="flex">
        <Sidebar activeModule={activeModule} onModuleChange={setActiveModule} />
        <main className="flex-1 p-6 ml-64">
          {renderActiveModule()}
        </main>
      </div>
    </div>
  );
}
