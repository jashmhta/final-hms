import {
  BarChart3,
  Users,
  UserCheck,
  Building,
  Calendar,
  CreditCard,
  Home,
  Stethoscope,
  Bed,
  Pill,
  FlaskConical,
  Scan,
  AlertTriangle,
  Shield,
  Bell,
  Settings,
  Building2
} from 'lucide-react';
import { Button } from './ui/button';
import { Separator } from './ui/separator';

interface SidebarProps {
  activeModule: string;
  onModuleChange: (module: string) => void;
}

const menuSections = [
  {
    title: 'Core Operations',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: Home },
      { id: 'patients', label: 'Patient Management', icon: Users },
      { id: 'appointments', label: 'Appointments', icon: Calendar },
      { id: 'doctors', label: 'Doctors & Staff', icon: UserCheck },
    ]
  },
  {
    title: 'Patient Care',
    items: [
      { id: 'opd', label: 'Outpatient (OPD)', icon: Stethoscope },
      { id: 'ipd', label: 'Inpatient (IPD)', icon: Bed },
      { id: 'emergency', label: 'Emergency', icon: AlertTriangle },
    ]
  },
  {
    title: 'Services & Departments',
    items: [
      { id: 'departments', label: 'Departments', icon: Building },
      { id: 'pharmacy', label: 'Pharmacy', icon: Pill },
      { id: 'laboratory', label: 'Laboratory', icon: FlaskConical },
      { id: 'radiology', label: 'Radiology', icon: Scan },
    ]
  },
  {
    title: 'Administration',
    items: [
      { id: 'billing', label: 'Billing & Accounts', icon: CreditCard },
      { id: 'reports', label: 'Reports & Analytics', icon: BarChart3 },
      { id: 'erp', label: 'ERP Management', icon: Building2 },
      { id: 'users', label: 'User Management', icon: Shield },
      { id: 'notifications', label: 'Notifications', icon: Bell },
      { id: 'settings', label: 'Settings', icon: Settings },
    ]
  }
];

export function Sidebar({ activeModule, onModuleChange }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
      <div className="p-4">
        <nav className="space-y-6">
          {menuSections.map((section, sectionIndex) => (
            <div key={section.title}>
              <h3 className="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3 px-2">
                {section.title}
              </h3>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeModule === item.id;

                  return (
                    <Button
                      key={item.id}
                      variant="ghost"
                      className={`w-full justify-start h-10 px-3 text-sm transition-colors ${
                        isActive
                          ? 'bg-teal-50 dark:bg-teal-900 text-teal-700 dark:text-teal-300 border-r-2 border-teal-500'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-teal-50 dark:hover:bg-teal-900 hover:text-teal-700 dark:hover:text-teal-300'
                      }`}
                      onClick={() => onModuleChange(item.id)}
                    >
                      <Icon className="h-4 w-4 mr-3 flex-shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </Button>
                  );
                })}
              </div>
              {sectionIndex < menuSections.length - 1 && (
                <Separator className="mt-4" />
              )}
            </div>
          ))}
        </nav>

        <div className="mt-8 p-4 bg-teal-50 dark:bg-teal-900 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <BarChart3 className="h-5 w-5 text-teal-600 dark:text-teal-400" />
            <span className="text-sm text-teal-800 dark:text-teal-200">Hospital Network</span>
          </div>
          <p className="text-xs text-teal-600 dark:text-teal-300">3 locations active</p>
          <div className="mt-2 w-full bg-teal-200 dark:bg-teal-700 rounded-full h-2">
            <div className="w-4/5 bg-teal-600 dark:bg-teal-400 h-2 rounded-full"></div>
          </div>
        </div>
      </div>
    </aside>
  );
}
