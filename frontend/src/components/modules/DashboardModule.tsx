import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Bell, Users, UserCheck, Building, Calendar, CreditCard, Plus, TrendingUp, AlertCircle, Activity } from 'lucide-react';

const keyStats = [
  { title: 'Total Patients', value: '2,847', icon: Users, color: 'text-blue-600', bgColor: 'bg-blue-100', change: '+12%' },
  { title: 'Active Doctors', value: '156', icon: UserCheck, color: 'text-green-600', bgColor: 'bg-green-100', change: '+3%' },
  { title: 'Departments', value: '18', icon: Building, color: 'text-purple-600', bgColor: 'bg-purple-100', change: '0%' },
  { title: 'Daily Appointments', value: '89', icon: Calendar, color: 'text-orange-600', bgColor: 'bg-orange-100', change: '+8%' },
  { title: 'Revenue (Monthly)', value: '$245K', icon: CreditCard, color: 'text-teal-600', bgColor: 'bg-teal-100', change: '+15%' },
];

const notifications = [
  { message: "Emergency: Patient in ICU requires immediate attention", type: 'emergency', time: '5 minutes ago' },
  { message: "Dr. Smith's schedule updated for tomorrow", type: 'schedule', time: '1 hour ago' },
  { message: "New patient registration: John Doe", type: 'new', time: '2 hours ago' },
  { message: "Equipment maintenance scheduled for OR-3", type: 'maintenance', time: '4 hours ago' },
  { message: "Monthly report generated successfully", type: 'report', time: '1 day ago' },
];

const quickActions = [
  { title: 'Register Patient', description: 'Add new patient to system', icon: Users, action: 'register-patient' },
  { title: 'Schedule Appointment', description: 'Book new patient appointment', icon: Calendar, action: 'schedule-appointment' },
  { title: 'Add Doctor', description: 'Register new medical staff', icon: UserCheck, action: 'add-doctor' },
  { title: 'Generate Report', description: 'Create financial or medical report', icon: TrendingUp, action: 'generate-report' },
];

const departmentOccupancy = [
  { name: 'Emergency', current: 24, capacity: 30, percentage: 80 },
  { name: 'ICU', current: 18, capacity: 20, percentage: 90 },
  { name: 'General Ward', current: 45, capacity: 60, percentage: 75 },
  { name: 'Pediatrics', current: 12, capacity: 20, percentage: 60 },
  { name: 'Maternity', current: 8, capacity: 15, percentage: 53 },
];

export function DashboardModule() {
  const userName = "Dr. Sarah Johnson";

  const getOccupancyColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600 bg-red-100';
    if (percentage >= 80) return 'text-orange-600 bg-orange-100';
    if (percentage >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  return (
    <div className="space-y-6">
      {/* Welcome Message */}
      <div className="bg-gradient-to-r from-teal-600 to-blue-600 rounded-lg p-6 text-white">
        <h1 className="text-2xl mb-2">Welcome back, {userName}!</h1>
        <p className="text-teal-100">Here's today's hospital overview and key metrics.</p>
      </div>

      {/* Key Stats */}
      <div>
        <h2 className="text-xl text-gray-900 mb-4">Key Performance Indicators</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {keyStats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">{stat.title}</p>
                      <p className="text-2xl text-gray-900">{stat.value}</p>
                      <p className={`text-sm ${stat.change.startsWith('+') ? 'text-green-600' : 'text-gray-600'}`}>
                        {stat.change} from last month
                      </p>
                    </div>
                    <div className={`w-12 h-12 ${stat.bgColor} rounded-lg flex items-center justify-center`}>
                      <Icon className={`h-6 w-6 ${stat.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Critical Alerts & Notifications */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2">
                <Bell className="h-5 w-5" />
                <span>Critical Alerts & Notifications</span>
              </CardTitle>
              <Badge variant="secondary" className="bg-red-100 text-red-800">
                {notifications.filter(n => n.type === 'emergency').length} Emergency
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {notifications.map((notification, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0 mt-1">
                    {notification.type === 'emergency' && <AlertCircle className="h-4 w-4 text-red-600" />}
                    {notification.type === 'schedule' && <Calendar className="h-4 w-4 text-blue-600" />}
                    {notification.type === 'new' && <Plus className="h-4 w-4 text-green-600" />}
                    {notification.type === 'maintenance' && <Building className="h-4 w-4 text-orange-600" />}
                    {notification.type === 'report' && <TrendingUp className="h-4 w-4 text-purple-600" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{notification.message}</p>
                    <p className="text-xs text-gray-500 mt-1">{notification.time}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-center">
              <Button variant="outline" size="sm">View All Notifications</Button>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {quickActions.map((action, index) => {
                const Icon = action.icon;
                return (
                  <Button
                    key={index}
                    variant="outline"
                    className="w-full justify-start h-auto p-4 text-left"
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-teal-100 rounded-lg flex items-center justify-center">
                          <Icon className="h-4 w-4 text-teal-600" />
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-gray-900">{action.title}</p>
                        <p className="text-xs text-gray-500">{action.description}</p>
                      </div>
                    </div>
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Department Occupancy & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Occupancy */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building className="h-5 w-5" />
              <span>Department Occupancy</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {departmentOccupancy.map((dept, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-900">{dept.name}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{dept.current}/{dept.capacity}</span>
                      <Badge className={getOccupancyColor(dept.percentage)}>
                        {dept.percentage}%
                      </Badge>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        dept.percentage >= 90 ? 'bg-red-600' :
                        dept.percentage >= 80 ? 'bg-orange-600' :
                        dept.percentage >= 70 ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${dept.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Patient Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Recent Patient Activity</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-900">Emergency Admission</p>
                  <p className="text-xs text-gray-500">Patient ID: #2847 - ICU</p>
                </div>
                <Badge className="bg-red-100 text-red-800">Critical</Badge>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-900">Surgery Completed</p>
                  <p className="text-xs text-gray-500">Patient ID: #2845 - OR-2</p>
                </div>
                <Badge className="bg-green-100 text-green-800">Completed</Badge>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-900">Discharge Processed</p>
                  <p className="text-xs text-gray-500">Patient ID: #2840 - General Ward</p>
                </div>
                <Badge className="bg-blue-100 text-blue-800">Discharged</Badge>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-900">Lab Results Ready</p>
                  <p className="text-xs text-gray-500">Patient ID: #2843 - Outpatient</p>
                </div>
                <Badge className="bg-orange-100 text-orange-800">Pending Review</Badge>
              </div>
            </div>
            <div className="mt-4 text-center">
              <Button variant="outline" size="sm">View All Activity</Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Today's Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Today's Appointments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Scheduled</span>
                <Badge variant="secondary" className="bg-blue-100 text-blue-800">89</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Completed</span>
                <Badge variant="secondary" className="bg-green-100 text-green-800">67</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Cancelled</span>
                <Badge variant="secondary" className="bg-red-100 text-red-800">3</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">No Show</span>
                <Badge variant="secondary" className="bg-gray-100 text-gray-800">2</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Financial Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Today's Revenue</span>
                <span className="text-gray-900">$12,450</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Pending Payments</span>
                <span className="text-orange-600">$3,240</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Outstanding Bills</span>
                <span className="text-red-600">$8,960</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Insurance Claims</span>
                <span className="text-blue-600">$15,680</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Staff on Duty</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Doctors</span>
                <Badge variant="secondary" className="bg-green-100 text-green-800">24 / 30</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Nurses</span>
                <Badge variant="secondary" className="bg-green-100 text-green-800">45 / 50</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Support Staff</span>
                <Badge variant="secondary" className="bg-green-100 text-green-800">18 / 20</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Emergency Team</span>
                <Badge variant="secondary" className="bg-orange-100 text-orange-800">6 / 8</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
