import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Textarea } from '../ui/textarea';
import { Users, UserPlus, Search, Filter, Eye, Edit, FileText, Calendar, Phone, Mail, MapPin, Activity, Heart, AlertTriangle } from 'lucide-react';

const patientsData = [
  {
    id: 'P-001',
    name: 'John Doe',
    age: 45,
    gender: 'Male',
    phone: '+1-555-0123',
    email: 'john.doe@email.com',
    address: '123 Main St, City, State',
    bloodType: 'A+',
    emergencyContact: 'Jane Doe - Wife',
    emergencyPhone: '+1-555-0124',
    admissionDate: '2024-01-15',
    status: 'Admitted',
    room: 'ICU-12',
    doctor: 'Dr. Smith',
    condition: 'Stable',
    insurance: 'BlueCross BlueShield',
    allergies: 'Penicillin, Nuts',
    lastVisit: '2024-01-20'
  },
  {
    id: 'P-002',
    name: 'Sarah Johnson',
    age: 32,
    gender: 'Female',
    phone: '+1-555-0125',
    email: 'sarah.j@email.com',
    address: '456 Oak Ave, City, State',
    bloodType: 'O-',
    emergencyContact: 'Mike Johnson - Husband',
    emergencyPhone: '+1-555-0126',
    admissionDate: '2024-01-18',
    status: 'Outpatient',
    room: 'N/A',
    doctor: 'Dr. Williams',
    condition: 'Good',
    insurance: 'Aetna',
    allergies: 'None',
    lastVisit: '2024-01-22'
  },
  {
    id: 'P-003',
    name: 'Michael Brown',
    age: 67,
    gender: 'Male',
    phone: '+1-555-0127',
    email: 'mbrown@email.com',
    address: '789 Pine St, City, State',
    bloodType: 'B+',
    emergencyContact: 'Lisa Brown - Daughter',
    emergencyPhone: '+1-555-0128',
    admissionDate: '2024-01-10',
    status: 'Discharged',
    room: 'N/A',
    doctor: 'Dr. Davis',
    condition: 'Recovered',
    insurance: 'Medicare',
    allergies: 'Shellfish',
    lastVisit: '2024-01-16'
  },
  {
    id: 'P-004',
    name: 'Emily Wilson',
    age: 28,
    gender: 'Female',
    phone: '+1-555-0129',
    email: 'emily.w@email.com',
    address: '321 Elm St, City, State',
    bloodType: 'AB+',
    emergencyContact: 'David Wilson - Father',
    emergencyPhone: '+1-555-0130',
    admissionDate: '2024-01-22',
    status: 'Emergency',
    room: 'ER-5',
    doctor: 'Dr. Lee',
    condition: 'Critical',
    insurance: 'United Healthcare',
    allergies: 'Latex',
    lastVisit: '2024-01-22'
  }
];

const bloodTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const doctors = ['Dr. Smith', 'Dr. Williams', 'Dr. Davis', 'Dr. Lee', 'Dr. Johnson', 'Dr. Brown'];

export function PatientsModule() {
  const [selectedPatient, setSelectedPatient] = useState<any>(null);
  const [isPatientDetailsOpen, setIsPatientDetailsOpen] = useState(false);
  const [isAddPatientOpen, setIsAddPatientOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [newPatient, setNewPatient] = useState({
    name: '',
    age: '',
    gender: '',
    phone: '',
    email: '',
    address: '',
    bloodType: '',
    emergencyContact: '',
    emergencyPhone: '',
    insurance: '',
    allergies: ''
  });

  const filteredPatients = patientsData.filter(patient => {
    const statusMatch = filterStatus === 'all' || patient.status.toLowerCase() === filterStatus.toLowerCase();
    const searchMatch = patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       patient.id.toLowerCase().includes(searchTerm.toLowerCase());
    return statusMatch && searchMatch;
  });

  const handleViewDetails = (patient: any) => {
    setSelectedPatient(patient);
    setIsPatientDetailsOpen(true);
  };

  const handleAddPatient = () => {
    console.log('Adding patient:', newPatient);
    setIsAddPatientOpen(false);
    setNewPatient({
      name: '',
      age: '',
      gender: '',
      phone: '',
      email: '',
      address: '',
      bloodType: '',
      emergencyContact: '',
      emergencyPhone: '',
      insurance: '',
      allergies: ''
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Admitted':
        return <Badge className="bg-blue-100 text-blue-800">Admitted</Badge>;
      case 'Outpatient':
        return <Badge className="bg-green-100 text-green-800">Outpatient</Badge>;
      case 'Emergency':
        return <Badge className="bg-red-100 text-red-800">Emergency</Badge>;
      case 'Discharged':
        return <Badge className="bg-gray-100 text-gray-800">Discharged</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const getConditionBadge = (condition: string) => {
    switch (condition) {
      case 'Critical':
        return <Badge className="bg-red-100 text-red-800">Critical</Badge>;
      case 'Stable':
        return <Badge className="bg-yellow-100 text-yellow-800">Stable</Badge>;
      case 'Good':
        return <Badge className="bg-green-100 text-green-800">Good</Badge>;
      case 'Recovered':
        return <Badge className="bg-blue-100 text-blue-800">Recovered</Badge>;
      default:
        return <Badge>{condition}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl text-gray-900">Patient Management</h2>
          <p className="text-gray-600">Manage patient records, medical history, and admissions</p>
        </div>
        <Dialog open={isAddPatientOpen} onOpenChange={setIsAddPatientOpen}>
          <DialogTrigger asChild>
            <Button className="bg-teal-600 hover:bg-teal-700">
              <UserPlus className="h-4 w-4 mr-2" />
              Register Patient
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Register New Patient</DialogTitle>
              <DialogDescription>
                Add a new patient to the hospital management system.
              </DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  value={newPatient.name}
                  onChange={(e) => setNewPatient({ ...newPatient, name: e.target.value })}
                  placeholder="John Doe"
                />
              </div>
              <div>
                <Label htmlFor="age">Age</Label>
                <Input
                  id="age"
                  type="number"
                  value={newPatient.age}
                  onChange={(e) => setNewPatient({ ...newPatient, age: e.target.value })}
                  placeholder="30"
                />
              </div>
              <div>
                <Label htmlFor="gender">Gender</Label>
                <Select value={newPatient.gender} onValueChange={(value) => setNewPatient({ ...newPatient, gender: value })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select gender" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Male">Male</SelectItem>
                    <SelectItem value="Female">Female</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="bloodType">Blood Type</Label>
                <Select value={newPatient.bloodType} onValueChange={(value) => setNewPatient({ ...newPatient, bloodType: value })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select blood type" />
                  </SelectTrigger>
                  <SelectContent>
                    {bloodTypes.map(type => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  value={newPatient.phone}
                  onChange={(e) => setNewPatient({ ...newPatient, phone: e.target.value })}
                  placeholder="+1-555-0123"
                />
              </div>
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={newPatient.email}
                  onChange={(e) => setNewPatient({ ...newPatient, email: e.target.value })}
                  placeholder="patient@email.com"
                />
              </div>
              <div className="col-span-2">
                <Label htmlFor="address">Address</Label>
                <Input
                  id="address"
                  value={newPatient.address}
                  onChange={(e) => setNewPatient({ ...newPatient, address: e.target.value })}
                  placeholder="123 Main St, City, State"
                />
              </div>
              <div>
                <Label htmlFor="emergencyContact">Emergency Contact</Label>
                <Input
                  id="emergencyContact"
                  value={newPatient.emergencyContact}
                  onChange={(e) => setNewPatient({ ...newPatient, emergencyContact: e.target.value })}
                  placeholder="Jane Doe - Wife"
                />
              </div>
              <div>
                <Label htmlFor="emergencyPhone">Emergency Phone</Label>
                <Input
                  id="emergencyPhone"
                  value={newPatient.emergencyPhone}
                  onChange={(e) => setNewPatient({ ...newPatient, emergencyPhone: e.target.value })}
                  placeholder="+1-555-0124"
                />
              </div>
              <div>
                <Label htmlFor="insurance">Insurance Provider</Label>
                <Input
                  id="insurance"
                  value={newPatient.insurance}
                  onChange={(e) => setNewPatient({ ...newPatient, insurance: e.target.value })}
                  placeholder="BlueCross BlueShield"
                />
              </div>
              <div>
                <Label htmlFor="allergies">Known Allergies</Label>
                <Input
                  id="allergies"
                  value={newPatient.allergies}
                  onChange={(e) => setNewPatient({ ...newPatient, allergies: e.target.value })}
                  placeholder="Penicillin, Nuts"
                />
              </div>
            </div>
            <div className="flex space-x-2 pt-4">
              <Button onClick={handleAddPatient} className="bg-teal-600 hover:bg-teal-700">
                Register Patient
              </Button>
              <Button variant="outline" onClick={() => setIsAddPatientOpen(false)}>
                Cancel
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Patient Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Patients</p>
                <p className="text-2xl text-gray-900">{patientsData.length}</p>
                <p className="text-sm text-blue-600">Registered</p>
              </div>
              <Users className="h-8 w-8 text-teal-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Currently Admitted</p>
                <p className="text-2xl text-gray-900">{patientsData.filter(p => p.status === 'Admitted').length}</p>
                <p className="text-sm text-green-600">In hospital</p>
              </div>
              <Activity className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Emergency Cases</p>
                <p className="text-2xl text-gray-900">{patientsData.filter(p => p.status === 'Emergency').length}</p>
                <p className="text-sm text-red-600">Critical attention</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Today's Discharges</p>
                <p className="text-2xl text-gray-900">{patientsData.filter(p => p.status === 'Discharged').length}</p>
                <p className="text-sm text-orange-600">Completed treatment</p>
              </div>
              <Heart className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Search & Filter Patients</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by name or patient ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="admitted">Admitted</SelectItem>
                  <SelectItem value="outpatient">Outpatient</SelectItem>
                  <SelectItem value="emergency">Emergency</SelectItem>
                  <SelectItem value="discharged">Discharged</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Patients Table */}
      <Card>
        <CardHeader>
          <CardTitle>Patient Directory ({filteredPatients.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Age/Gender</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Doctor</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Condition</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPatients.map((patient) => (
                <TableRow key={patient.id}>
                  <TableCell className="text-gray-900">{patient.id}</TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{patient.name}</p>
                      <p className="text-sm text-gray-500">Blood: {patient.bloodType}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{patient.age} years</p>
                      <p className="text-sm text-gray-500">{patient.gender}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center space-x-1">
                        <Phone className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-600">{patient.phone}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Mail className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-600">{patient.email}</span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{patient.doctor}</p>
                      <p className="text-sm text-gray-500">{patient.room !== 'N/A' ? patient.room : 'Outpatient'}</p>
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(patient.status)}</TableCell>
                  <TableCell>{getConditionBadge(patient.condition)}</TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button variant="ghost" size="sm" onClick={() => handleViewDetails(patient)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <FileText className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Patient Details Dialog */}
      <Dialog open={isPatientDetailsOpen} onOpenChange={setIsPatientDetailsOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{selectedPatient?.name} - Patient Details</DialogTitle>
            <DialogDescription>
              Comprehensive patient information and medical records.
            </DialogDescription>
          </DialogHeader>
          {selectedPatient && (
            <div className="space-y-6">
              {/* Personal Information */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Personal Information</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Patient ID</Label>
                    <p className="text-gray-900">{selectedPatient.id}</p>
                  </div>
                  <div>
                    <Label>Full Name</Label>
                    <p className="text-gray-900">{selectedPatient.name}</p>
                  </div>
                  <div>
                    <Label>Age & Gender</Label>
                    <p className="text-gray-900">{selectedPatient.age} years, {selectedPatient.gender}</p>
                  </div>
                  <div>
                    <Label>Blood Type</Label>
                    <p className="text-gray-900">{selectedPatient.bloodType}</p>
                  </div>
                  <div>
                    <Label>Phone</Label>
                    <p className="text-gray-900">{selectedPatient.phone}</p>
                  </div>
                  <div>
                    <Label>Email</Label>
                    <p className="text-gray-900">{selectedPatient.email}</p>
                  </div>
                  <div className="col-span-3">
                    <Label>Address</Label>
                    <p className="text-gray-900">{selectedPatient.address}</p>
                  </div>
                </div>
              </div>

              {/* Medical Information */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Medical Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Current Status</Label>
                    <div className="mt-1">{getStatusBadge(selectedPatient.status)}</div>
                  </div>
                  <div>
                    <Label>Condition</Label>
                    <div className="mt-1">{getConditionBadge(selectedPatient.condition)}</div>
                  </div>
                  <div>
                    <Label>Assigned Doctor</Label>
                    <p className="text-gray-900">{selectedPatient.doctor}</p>
                  </div>
                  <div>
                    <Label>Room/Location</Label>
                    <p className="text-gray-900">{selectedPatient.room}</p>
                  </div>
                  <div>
                    <Label>Admission Date</Label>
                    <p className="text-gray-900">{new Date(selectedPatient.admissionDate).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <Label>Last Visit</Label>
                    <p className="text-gray-900">{new Date(selectedPatient.lastVisit).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <Label>Insurance Provider</Label>
                    <p className="text-gray-900">{selectedPatient.insurance}</p>
                  </div>
                  <div>
                    <Label>Known Allergies</Label>
                    <p className="text-gray-900">{selectedPatient.allergies}</p>
                  </div>
                </div>
              </div>

              {/* Emergency Contact */}
              <div>
                <h3 className="text-lg text-gray-900 mb-3">Emergency Contact</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Emergency Contact</Label>
                    <p className="text-gray-900">{selectedPatient.emergencyContact}</p>
                  </div>
                  <div>
                    <Label>Emergency Phone</Label>
                    <p className="text-gray-900">{selectedPatient.emergencyPhone}</p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-2">
                <Button className="bg-teal-600 hover:bg-teal-700">
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Patient
                </Button>
                <Button variant="outline">
                  <FileText className="h-4 w-4 mr-2" />
                  Medical Records
                </Button>
                <Button variant="outline">
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Appointment
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
