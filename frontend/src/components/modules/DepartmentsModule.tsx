import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Building, Plus, Eye, Edit, Users, Bed, Activity, DollarSign, UserCheck, Settings, AlertCircle, TrendingUp } from 'lucide-react';

const departmentsData = [
  {
    id: 'DEPT-001',
    name: 'Emergency Department',
    head: 'Dr. Michael Davis',
    totalBeds: 30,
    occupiedBeds: 24,
    totalStaff: 35,
    onDutyStaff: 28,
    monthlyRevenue: 125000,
    patientsToday: 45,
    avgWaitTime: '15 mins',
    status: 'Active',
    location: 'Ground Floor - East Wing',
    equipment: ['X-Ray Machine', 'ECG', 'Defibrillators', 'Ventilators'],
    services: ['Emergency Care', 'Trauma Treatment', 'Critical Care'],
    operatingHours: '24/7'
  },
  {
    id: 'DEPT-002',
    name: 'Cardiology',
    head: 'Dr. James Smith',
    totalBeds: 20,
    occupiedBeds: 15,
    totalStaff: 18,
    onDutyStaff: 12,
    monthlyRevenue: 180000,
    patientsToday: 25,
    avgWaitTime: '25 mins',
    status: 'Active',
    location: '3rd Floor - North Wing',
    equipment: ['Catheterization Lab', 'Echocardiogram', 'Stress Test Equipment'],
    services: ['Cardiac Surgery', 'Catheterization', 'Pacemaker Implantation'],
    operatingHours: 'Mon-Fri: 8AM-6PM'
  },
  {
    id: 'DEPT-003',
    name: 'Pediatrics',
    head: 'Dr. Sarah Williams',
    totalBeds: 25,
    occupiedBeds: 18,
    totalStaff: 22,
    onDutyStaff: 20,
    monthlyRevenue: 95000,
    patientsToday: 32,
    avgWaitTime: '20 mins',
    status: 'Active',
    location: '2nd Floor - South Wing',
    equipment: ['Pediatric Ventilators', 'Incubators', 'Neonatal Monitors'],
    services: ['Child Care', 'Vaccination', 'Neonatal Care'],
    operatingHours: 'Mon-Sat: 8AM-8PM'
  },
  {
    id: 'DEPT-004',
    name: 'Orthopedics',
    head: 'Dr. Robert Johnson',
    totalBeds: 15,
    occupiedBeds: 8,
    totalStaff: 12,
    onDutyStaff: 8,
    monthlyRevenue: 140000,
    patientsToday: 12,
    avgWaitTime: '30 mins',
    status: 'Maintenance',
    location: '5th Floor - West Wing',
    equipment: ['X-Ray', 'MRI Scanner', 'Surgical Equipment'],
    services: ['Bone Surgery', 'Joint Replacement', 'Sports Medicine'],
    operatingHours: 'Mon-Fri: 8AM-4PM'
  },
  {
    id: 'DEPT-005',
    name: 'Neurology',
    head: 'Dr. Emily Lee',
    totalBeds: 18,
    occupiedBeds: 12,
    totalStaff: 15,
    onDutyStaff: 10,
    monthlyRevenue: 160000,
    patientsToday: 18,
    avgWaitTime: '35 mins',
    status: 'Active',
    location: '4th Floor - North Wing',
    equipment: ['EEG Machine', 'CT Scanner', 'Neurosurgical Equipment'],
    services: ['Brain Surgery', 'Stroke Treatment', 'Neurological Assessment'],
    operatingHours: 'Tue-Sat: 9AM-5PM'
  }
];

export function DepartmentsModule() {
  const [selectedDepartment, setSelectedDepartment] = useState<any>(null);
  const [isDepartmentDetailsOpen, setIsDepartmentDetailsOpen] = useState(false);
  const [isAddDepartmentOpen, setIsAddDepartmentOpen] = useState(false);
  const [newDepartment, setNewDepartment] = useState({
    name: '',
    head: '',
    totalBeds: '',
    totalStaff: '',
    location: '',
    operatingHours: ''
  });

  const handleViewDetails = (department: any) => {
    setSelectedDepartment(department);
    setIsDepartmentDetailsOpen(true);
  };

  const handleAddDepartment = () => {
    console.log('Adding department:', newDepartment);
    setIsAddDepartmentOpen(false);
    setNewDepartment({
      name: '',
      head: '',
      totalBeds: '',
      totalStaff: '',
      location: '',
      operatingHours: ''
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Active':
        return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'Maintenance':
        return <Badge className="bg-orange-100 text-orange-800">Maintenance</Badge>;
      case 'Closed':
        return <Badge className="bg-red-100 text-red-800">Closed</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const getOccupancyRate = (occupied: number, total: number) => {
    return Math.round((occupied / total) * 100);
  };

  const getOccupancyColor = (rate: number) => {
    if (rate >= 90) return 'text-red-600';
    if (rate >= 80) return 'text-orange-600';
    if (rate >= 70) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl text-gray-900">Hospital Departments</h2>
          <p className="text-gray-600">Manage departments, services, and operational capacity</p>
        </div>
        <Dialog open={isAddDepartmentOpen} onOpenChange={setIsAddDepartmentOpen}>
          <DialogTrigger asChild>
            <Button className="bg-teal-600 hover:bg-teal-700">
              <Plus className="h-4 w-4 mr-2" />
              Add Department
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Add New Department</DialogTitle>
              <DialogDescription>
                Create a new hospital department with initial configuration.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Department Name</Label>
                  <Input
                    id="name"
                    value={newDepartment.name}
                    onChange={(e) => setNewDepartment({ ...newDepartment, name: e.target.value })}
                    placeholder="e.g., Radiology"
                  />
                </div>
                <div>
                  <Label htmlFor="head">Department Head</Label>
                  <Input
                    id="head"
                    value={newDepartment.head}
                    onChange={(e) => setNewDepartment({ ...newDepartment, head: e.target.value })}
                    placeholder="Dr. John Smith"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="totalBeds">Total Beds</Label>
                  <Input
                    id="totalBeds"
                    type="number"
                    value={newDepartment.totalBeds}
                    onChange={(e) => setNewDepartment({ ...newDepartment, totalBeds: e.target.value })}
                    placeholder="20"
                  />
                </div>
                <div>
                  <Label htmlFor="totalStaff">Total Staff</Label>
                  <Input
                    id="totalStaff"
                    type="number"
                    value={newDepartment.totalStaff}
                    onChange={(e) => setNewDepartment({ ...newDepartment, totalStaff: e.target.value })}
                    placeholder="15"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  value={newDepartment.location}
                  onChange={(e) => setNewDepartment({ ...newDepartment, location: e.target.value })}
                  placeholder="3rd Floor - North Wing"
                />
              </div>
              <div>
                <Label htmlFor="operatingHours">Operating Hours</Label>
                <Input
                  id="operatingHours"
                  value={newDepartment.operatingHours}
                  onChange={(e) => setNewDepartment({ ...newDepartment, operatingHours: e.target.value })}
                  placeholder="Mon-Fri: 8AM-6PM"
                />
              </div>
              <div className="flex space-x-2 pt-4">
                <Button onClick={handleAddDepartment} className="bg-teal-600 hover:bg-teal-700">
                  Add Department
                </Button>
                <Button variant="outline" onClick={() => setIsAddDepartmentOpen(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Department Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Departments</p>
                <p className="text-2xl text-gray-900">{departmentsData.length}</p>
                <p className="text-sm text-blue-600">Operational units</p>
              </div>
              <Building className="h-8 w-8 text-teal-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Beds</p>
                <p className="text-2xl text-gray-900">{departmentsData.reduce((sum, dept) => sum + dept.totalBeds, 0)}</p>
                <p className="text-sm text-green-600">Hospital capacity</p>
              </div>
              <Bed className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Occupied Beds</p>
                <p className="text-2xl text-gray-900">{departmentsData.reduce((sum, dept) => sum + dept.occupiedBeds, 0)}</p>
                <p className="text-sm text-purple-600">Currently in use</p>
              </div>
              <Activity className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Monthly Revenue</p>
                <p className="text-2xl text-gray-900">${(departmentsData.reduce((sum, dept) => sum + dept.monthlyRevenue, 0) / 1000).toFixed(0)}K</p>
                <p className="text-sm text-orange-600">Combined total</p>
              </div>
              <DollarSign className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Department Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {departmentsData.map((department) => (
          <Card key={department.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{department.name}</CardTitle>
                {getStatusBadge(department.status)}
              </div>
              <p className="text-sm text-gray-600">Head: {department.head}</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Bed Occupancy */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-600">Bed Occupancy</span>
                    <span className={`text-sm ${getOccupancyColor(getOccupancyRate(department.occupiedBeds, department.totalBeds))}`}>
                      {getOccupancyRate(department.occupiedBeds, department.totalBeds)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-teal-600 h-2 rounded-full"
                      style={{ width: `${getOccupancyRate(department.occupiedBeds, department.totalBeds)}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{department.occupiedBeds} / {department.totalBeds} beds</p>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-lg text-gray-900">{department.patientsToday}</p>
                    <p className="text-xs text-gray-600">Patients Today</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-lg text-gray-900">{department.avgWaitTime}</p>
                    <p className="text-xs text-gray-600">Avg Wait Time</p>
                  </div>
                </div>

                {/* Staff Status */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1">
                    <UserCheck className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-gray-600">Staff on Duty</span>
                  </div>
                  <span className="text-sm text-gray-900">{department.onDutyStaff} / {department.totalStaff}</span>
                </div>

                {/* Revenue */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-gray-600">Monthly Revenue</span>
                  </div>
                  <span className="text-sm text-gray-900">${(department.monthlyRevenue / 1000).toFixed(0)}K</span>
                </div>

                <Button
                  variant="outline"
                  className="w-full mt-4"
                  onClick={() => handleViewDetails(department)}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View Details
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Departments Table */}
      <Card>
        <CardHeader>
          <CardTitle>Department Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Department</TableHead>
                <TableHead>Head</TableHead>
                <TableHead>Capacity</TableHead>
                <TableHead>Staff</TableHead>
                <TableHead>Today's Load</TableHead>
                <TableHead>Revenue</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {departmentsData.map((department) => (
                <TableRow key={department.id}>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{department.name}</p>
                      <p className="text-sm text-gray-500">{department.location}</p>
                    </div>
                  </TableCell>
                  <TableCell className="text-gray-900">{department.head}</TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{department.occupiedBeds} / {department.totalBeds}</p>
                      <p className={`text-sm ${getOccupancyColor(getOccupancyRate(department.occupiedBeds, department.totalBeds))}`}>
                        {getOccupancyRate(department.occupiedBeds, department.totalBeds)}% occupied
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{department.onDutyStaff} / {department.totalStaff}</p>
                      <p className="text-sm text-gray-500">on duty</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{department.patientsToday} patients</p>
                      <p className="text-sm text-gray-500">{department.avgWaitTime} wait</p>
                    </div>
                  </TableCell>
                  <TableCell className="text-gray-900">${(department.monthlyRevenue / 1000).toFixed(0)}K</TableCell>
                  <TableCell>{getStatusBadge(department.status)}</TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button variant="ghost" size="sm" onClick={() => handleViewDetails(department)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Department Details Dialog */}
      <Dialog open={isDepartmentDetailsOpen} onOpenChange={setIsDepartmentDetailsOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{selectedDepartment?.name} - Department Details</DialogTitle>
            <DialogDescription>
              Comprehensive department information and operational metrics.
            </DialogDescription>
          </DialogHeader>
          {selectedDepartment && (
            <div className="space-y-6">
              {/* Basic Information */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Department Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Department ID</Label>
                    <p className="text-gray-900">{selectedDepartment.id}</p>
                  </div>
                  <div>
                    <Label>Department Name</Label>
                    <p className="text-gray-900">{selectedDepartment.name}</p>
                  </div>
                  <div>
                    <Label>Department Head</Label>
                    <p className="text-gray-900">{selectedDepartment.head}</p>
                  </div>
                  <div>
                    <Label>Location</Label>
                    <p className="text-gray-900">{selectedDepartment.location}</p>
                  </div>
                  <div>
                    <Label>Operating Hours</Label>
                    <p className="text-gray-900">{selectedDepartment.operatingHours}</p>
                  </div>
                  <div>
                    <Label>Status</Label>
                    <div className="mt-1">{getStatusBadge(selectedDepartment.status)}</div>
                  </div>
                </div>
              </div>

              {/* Capacity & Utilization */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Capacity & Utilization</h3>
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">{selectedDepartment.totalBeds}</p>
                    <p className="text-sm text-gray-600">Total Beds</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">{selectedDepartment.occupiedBeds}</p>
                    <p className="text-sm text-gray-600">Occupied Beds</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">{selectedDepartment.totalStaff}</p>
                    <p className="text-sm text-gray-600">Total Staff</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">{selectedDepartment.onDutyStaff}</p>
                    <p className="text-sm text-gray-600">On Duty</p>
                  </div>
                </div>
              </div>

              {/* Services & Equipment */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Services & Equipment</h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <Label>Services Offered</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {selectedDepartment.services?.map((service: string, index: number) => (
                        <Badge key={index} variant="outline" className="bg-blue-50 text-blue-700">
                          {service}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <Label>Equipment Available</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {selectedDepartment.equipment?.map((item: string, index: number) => (
                        <Badge key={index} variant="outline" className="bg-green-50 text-green-700">
                          {item}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Performance Metrics</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">{selectedDepartment.patientsToday}</p>
                    <p className="text-sm text-gray-600">Patients Today</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">{selectedDepartment.avgWaitTime}</p>
                    <p className="text-sm text-gray-600">Avg Wait Time</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">${(selectedDepartment.monthlyRevenue / 1000).toFixed(0)}K</p>
                    <p className="text-sm text-gray-600">Monthly Revenue</p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-2">
                <Button className="bg-teal-600 hover:bg-teal-700">
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Department
                </Button>
                <Button variant="outline">
                  <Users className="h-4 w-4 mr-2" />
                  Manage Staff
                </Button>
                <Button variant="outline">
                  <Settings className="h-4 w-4 mr-2" />
                  Department Settings
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
