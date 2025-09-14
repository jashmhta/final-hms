import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { UserCheck, Plus, Eye, Edit, Calendar, Phone, Mail, MapPin, Star, Clock, Users, Stethoscope, Award } from 'lucide-react';

const doctorsData = [
  {
    id: 'D-001',
    name: 'Dr. James Smith',
    specialty: 'Cardiology',
    department: 'Cardiology',
    experience: '15 years',
    qualification: 'MBBS, MD Cardiology, FACC',
    phone: '+1-555-1001',
    email: 'james.smith@hospital.com',
    schedule: 'Mon-Fri: 9AM-5PM',
    rating: 4.8,
    patientsToday: 12,
    appointmentsToday: 15,
    status: 'Available',
    room: 'Room 301',
    licenseNumber: 'MD123456',
    joinDate: '2019-03-15'
  },
  {
    id: 'D-002',
    name: 'Dr. Sarah Williams',
    specialty: 'Pediatrics',
    department: 'Pediatrics',
    experience: '10 years',
    qualification: 'MBBS, MD Pediatrics, FAAP',
    phone: '+1-555-1002',
    email: 'sarah.williams@hospital.com',
    schedule: 'Mon-Sat: 8AM-4PM',
    rating: 4.9,
    patientsToday: 18,
    appointmentsToday: 20,
    status: 'Busy',
    room: 'Room 205',
    licenseNumber: 'MD123457',
    joinDate: '2020-01-10'
  },
  {
    id: 'D-003',
    name: 'Dr. Michael Davis',
    specialty: 'Emergency Medicine',
    department: 'Emergency',
    experience: '8 years',
    qualification: 'MBBS, MD Emergency Medicine',
    phone: '+1-555-1003',
    email: 'michael.davis@hospital.com',
    schedule: '24/7 Shifts',
    rating: 4.7,
    patientsToday: 25,
    appointmentsToday: 0,
    status: 'On Duty',
    room: 'ER-Main',
    licenseNumber: 'MD123458',
    joinDate: '2021-06-20'
  },
  {
    id: 'D-004',
    name: 'Dr. Emily Lee',
    specialty: 'Neurology',
    department: 'Neurology',
    experience: '12 years',
    qualification: 'MBBS, MD Neurology, FAAN',
    phone: '+1-555-1004',
    email: 'emily.lee@hospital.com',
    schedule: 'Tue-Sat: 10AM-6PM',
    rating: 4.6,
    patientsToday: 8,
    appointmentsToday: 10,
    status: 'Available',
    room: 'Room 401',
    licenseNumber: 'MD123459',
    joinDate: '2018-09-05'
  },
  {
    id: 'D-005',
    name: 'Dr. Robert Johnson',
    specialty: 'Orthopedics',
    department: 'Orthopedics',
    experience: '20 years',
    qualification: 'MBBS, MS Orthopedics, FAAOS',
    phone: '+1-555-1005',
    email: 'robert.johnson@hospital.com',
    schedule: 'Mon-Fri: 8AM-3PM',
    rating: 4.9,
    patientsToday: 6,
    appointmentsToday: 8,
    status: 'On Leave',
    room: 'Room 501',
    licenseNumber: 'MD123460',
    joinDate: '2015-11-12'
  }
];

const specialties = [
  'Cardiology',
  'Pediatrics',
  'Emergency Medicine',
  'Neurology',
  'Orthopedics',
  'Internal Medicine',
  'Surgery',
  'Radiology',
  'Psychiatry',
  'Dermatology'
];

const departments = [
  'Cardiology',
  'Pediatrics',
  'Emergency',
  'Neurology',
  'Orthopedics',
  'Internal Medicine',
  'Surgery',
  'Radiology',
  'Psychiatry',
  'Dermatology'
];

export function DoctorsModule() {
  const [selectedDoctor, setSelectedDoctor] = useState<any>(null);
  const [isDoctorDetailsOpen, setIsDoctorDetailsOpen] = useState(false);
  const [isAddDoctorOpen, setIsAddDoctorOpen] = useState(false);
  const [filterDepartment, setFilterDepartment] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [newDoctor, setNewDoctor] = useState({
    name: '',
    specialty: '',
    department: '',
    qualification: '',
    phone: '',
    email: '',
    licenseNumber: '',
    experience: ''
  });

  const filteredDoctors = doctorsData.filter(doctor => {
    const departmentMatch = filterDepartment === 'all' || doctor.department === filterDepartment;
    const statusMatch = filterStatus === 'all' || doctor.status.toLowerCase() === filterStatus.toLowerCase();
    return departmentMatch && statusMatch;
  });

  const handleViewDetails = (doctor: any) => {
    setSelectedDoctor(doctor);
    setIsDoctorDetailsOpen(true);
  };

  const handleAddDoctor = () => {
    console.log('Adding doctor:', newDoctor);
    setIsAddDoctorOpen(false);
    setNewDoctor({
      name: '',
      specialty: '',
      department: '',
      qualification: '',
      phone: '',
      email: '',
      licenseNumber: '',
      experience: ''
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Available':
        return <Badge className="bg-green-100 text-green-800">Available</Badge>;
      case 'Busy':
        return <Badge className="bg-orange-100 text-orange-800">Busy</Badge>;
      case 'On Duty':
        return <Badge className="bg-blue-100 text-blue-800">On Duty</Badge>;
      case 'On Leave':
        return <Badge className="bg-gray-100 text-gray-800">On Leave</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl text-gray-900">Medical Staff</h2>
          <p className="text-gray-600">Manage doctors, schedules, and medical staff assignments</p>
        </div>
        <Dialog open={isAddDoctorOpen} onOpenChange={setIsAddDoctorOpen}>
          <DialogTrigger asChild>
            <Button className="bg-teal-600 hover:bg-teal-700">
              <Plus className="h-4 w-4 mr-2" />
              Add Doctor
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Add New Doctor</DialogTitle>
              <DialogDescription>
                Register a new medical professional to join the hospital staff.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={newDoctor.name}
                    onChange={(e) => setNewDoctor({ ...newDoctor, name: e.target.value })}
                    placeholder="Dr. John Smith"
                  />
                </div>
                <div>
                  <Label htmlFor="specialty">Specialty</Label>
                  <Select value={newDoctor.specialty} onValueChange={(value) => setNewDoctor({ ...newDoctor, specialty: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select specialty" />
                    </SelectTrigger>
                    <SelectContent>
                      {specialties.map(specialty => (
                        <SelectItem key={specialty} value={specialty}>{specialty}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="department">Department</Label>
                  <Select value={newDoctor.department} onValueChange={(value) => setNewDoctor({ ...newDoctor, department: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select department" />
                    </SelectTrigger>
                    <SelectContent>
                      {departments.map(dept => (
                        <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="experience">Experience</Label>
                  <Input
                    id="experience"
                    value={newDoctor.experience}
                    onChange={(e) => setNewDoctor({ ...newDoctor, experience: e.target.value })}
                    placeholder="5 years"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="qualification">Qualifications</Label>
                <Input
                  id="qualification"
                  value={newDoctor.qualification}
                  onChange={(e) => setNewDoctor({ ...newDoctor, qualification: e.target.value })}
                  placeholder="MBBS, MD Cardiology"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    value={newDoctor.phone}
                    onChange={(e) => setNewDoctor({ ...newDoctor, phone: e.target.value })}
                    placeholder="+1-555-1001"
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={newDoctor.email}
                    onChange={(e) => setNewDoctor({ ...newDoctor, email: e.target.value })}
                    placeholder="doctor@hospital.com"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="licenseNumber">Medical License Number</Label>
                <Input
                  id="licenseNumber"
                  value={newDoctor.licenseNumber}
                  onChange={(e) => setNewDoctor({ ...newDoctor, licenseNumber: e.target.value })}
                  placeholder="MD123456"
                />
              </div>
              <div className="flex space-x-2 pt-4">
                <Button onClick={handleAddDoctor} className="bg-teal-600 hover:bg-teal-700">
                  Add Doctor
                </Button>
                <Button variant="outline" onClick={() => setIsAddDoctorOpen(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Doctor Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Doctors</p>
                <p className="text-2xl text-gray-900">{doctorsData.length}</p>
                <p className="text-sm text-blue-600">Medical staff</p>
              </div>
              <UserCheck className="h-8 w-8 text-teal-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">On Duty Today</p>
                <p className="text-2xl text-gray-900">{doctorsData.filter(d => d.status !== 'On Leave').length}</p>
                <p className="text-sm text-green-600">Available</p>
              </div>
              <Clock className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Today's Patients</p>
                <p className="text-2xl text-gray-900">{doctorsData.reduce((sum, doctor) => sum + doctor.patientsToday, 0)}</p>
                <p className="text-sm text-purple-600">Being treated</p>
              </div>
              <Users className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Rating</p>
                <p className="text-2xl text-gray-900">{(doctorsData.reduce((sum, doctor) => sum + doctor.rating, 0) / doctorsData.length).toFixed(1)}</p>
                <p className="text-sm text-orange-600">Patient satisfaction</p>
              </div>
              <Star className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <Label>Department</Label>
              <Select value={filterDepartment} onValueChange={setFilterDepartment}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Departments</SelectItem>
                  {departments.map(dept => (
                    <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <Label>Status</Label>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="available">Available</SelectItem>
                  <SelectItem value="busy">Busy</SelectItem>
                  <SelectItem value="on duty">On Duty</SelectItem>
                  <SelectItem value="on leave">On Leave</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Doctors Table */}
      <Card>
        <CardHeader>
          <CardTitle>Medical Staff Directory ({filteredDoctors.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Doctor</TableHead>
                <TableHead>Specialty</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Today's Load</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDoctors.map((doctor) => (
                <TableRow key={doctor.id}>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{doctor.name}</p>
                      <p className="text-sm text-gray-500">{doctor.experience} experience</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 mb-1">
                        {doctor.specialty}
                      </Badge>
                      <p className="text-sm text-gray-500">{doctor.department}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center space-x-1">
                        <Phone className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-600">{doctor.phone}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Mail className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-600">{doctor.email}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <MapPin className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-600">{doctor.room}</span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <p className="text-sm text-gray-900">{doctor.patientsToday} patients</p>
                      <p className="text-xs text-gray-500">{doctor.appointmentsToday} appointments</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      <Star className="h-4 w-4 text-yellow-400 fill-current" />
                      <span className="text-gray-900">{doctor.rating}</span>
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(doctor.status)}</TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button variant="ghost" size="sm" onClick={() => handleViewDetails(doctor)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Calendar className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Doctor Details Dialog */}
      <Dialog open={isDoctorDetailsOpen} onOpenChange={setIsDoctorDetailsOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{selectedDoctor?.name} - Profile</DialogTitle>
            <DialogDescription>
              Comprehensive doctor information and performance metrics.
            </DialogDescription>
          </DialogHeader>
          {selectedDoctor && (
            <div className="space-y-6">
              {/* Professional Information */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Professional Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Doctor ID</Label>
                    <p className="text-gray-900">{selectedDoctor.id}</p>
                  </div>
                  <div>
                    <Label>Full Name</Label>
                    <p className="text-gray-900">{selectedDoctor.name}</p>
                  </div>
                  <div>
                    <Label>Specialty</Label>
                    <p className="text-gray-900">{selectedDoctor.specialty}</p>
                  </div>
                  <div>
                    <Label>Department</Label>
                    <p className="text-gray-900">{selectedDoctor.department}</p>
                  </div>
                  <div>
                    <Label>Experience</Label>
                    <p className="text-gray-900">{selectedDoctor.experience}</p>
                  </div>
                  <div>
                    <Label>Qualifications</Label>
                    <p className="text-gray-900">{selectedDoctor.qualification}</p>
                  </div>
                  <div>
                    <Label>Medical License</Label>
                    <p className="text-gray-900">{selectedDoctor.licenseNumber}</p>
                  </div>
                  <div>
                    <Label>Join Date</Label>
                    <p className="text-gray-900">{new Date(selectedDoctor.joinDate).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>

              {/* Contact & Schedule */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Contact & Schedule</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Phone</Label>
                    <p className="text-gray-900">{selectedDoctor.phone}</p>
                  </div>
                  <div>
                    <Label>Email</Label>
                    <p className="text-gray-900">{selectedDoctor.email}</p>
                  </div>
                  <div>
                    <Label>Room/Office</Label>
                    <p className="text-gray-900">{selectedDoctor.room}</p>
                  </div>
                  <div>
                    <Label>Schedule</Label>
                    <p className="text-gray-900">{selectedDoctor.schedule}</p>
                  </div>
                  <div>
                    <Label>Current Status</Label>
                    <div className="mt-1">{getStatusBadge(selectedDoctor.status)}</div>
                  </div>
                  <div>
                    <Label>Patient Rating</Label>
                    <div className="flex items-center space-x-1">
                      <Star className="h-4 w-4 text-yellow-400 fill-current" />
                      <span className="text-gray-900">{selectedDoctor.rating} / 5.0</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Today's Metrics */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Today's Metrics</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">{selectedDoctor.patientsToday}</p>
                    <p className="text-sm text-gray-600">Patients Seen</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">{selectedDoctor.appointmentsToday}</p>
                    <p className="text-sm text-gray-600">Appointments</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl text-gray-900">{selectedDoctor.rating}</p>
                    <p className="text-sm text-gray-600">Avg Rating</p>
                  </div>
                </div>
              </div>

              {/* Credentials */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Professional Credentials</h3>
                <div className="grid grid-cols-3 gap-3">
                  <div className="flex items-center space-x-2 p-3 border rounded-lg">
                    <Award className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="text-sm text-gray-900">Medical Degree</p>
                      <p className="text-xs text-gray-500">MBBS Certified</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 p-3 border rounded-lg">
                    <Stethoscope className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="text-sm text-gray-900">Specialty License</p>
                      <p className="text-xs text-gray-500">Valid until 2025</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 p-3 border rounded-lg">
                    <Award className="h-5 w-5 text-purple-600" />
                    <div>
                      <p className="text-sm text-gray-900">Board Certification</p>
                      <p className="text-xs text-gray-500">Active</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-2">
                <Button className="bg-teal-600 hover:bg-teal-700">
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Profile
                </Button>
                <Button variant="outline">
                  <Calendar className="h-4 w-4 mr-2" />
                  View Schedule
                </Button>
                <Button variant="outline">
                  <Users className="h-4 w-4 mr-2" />
                  Patient List
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
