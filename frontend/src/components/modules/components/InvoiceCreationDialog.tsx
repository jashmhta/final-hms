import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { RadioGroup, RadioGroupItem } from '../../ui/radio-group';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Plus, X, UserPlus, UserCheck, Trash2, Calculator } from 'lucide-react';

// Department services with pricing
const departmentServices = {
  cardiology: {
    name: 'Cardiology',
    services: [
      { id: 'card_01', name: 'Cardiology Consultation', price: 250 },
      { id: 'card_02', name: 'ECG Test', price: 150 },
      { id: 'card_03', name: 'Echo Cardiogram', price: 400 },
      { id: 'card_04', name: 'Stress Test', price: 350 },
      { id: 'card_05', name: 'Holter Monitor', price: 300 },
    ]
  },
  pediatrics: {
    name: 'Pediatrics',
    services: [
      { id: 'ped_01', name: 'Pediatric Consultation', price: 200 },
      { id: 'ped_02', name: 'Vaccination', price: 75 },
      { id: 'ped_03', name: 'Growth Assessment', price: 100 },
      { id: 'ped_04', name: 'Developmental Screening', price: 150 },
      { id: 'ped_05', name: 'Pediatric Emergency Care', price: 300 },
    ]
  },
  emergency: {
    name: 'Emergency',
    services: [
      { id: 'emer_01', name: 'Emergency Consultation', price: 400 },
      { id: 'emer_02', name: 'Trauma Care', price: 800 },
      { id: 'emer_03', name: 'Suturing', price: 200 },
      { id: 'emer_04', name: 'Emergency X-Ray', price: 250 },
      { id: 'emer_05', name: 'Emergency Blood Work', price: 180 },
    ]
  },
  neurology: {
    name: 'Neurology',
    services: [
      { id: 'neuro_01', name: 'Neurology Consultation', price: 300 },
      { id: 'neuro_02', name: 'MRI Scan', price: 1200 },
      { id: 'neuro_03', name: 'CT Scan', price: 800 },
      { id: 'neuro_04', name: 'EEG Test', price: 450 },
      { id: 'neuro_05', name: 'Lumbar Puncture', price: 600 },
    ]
  },
  orthopedics: {
    name: 'Orthopedics',
    services: [
      { id: 'ortho_01', name: 'Orthopedic Consultation', price: 280 },
      { id: 'ortho_02', name: 'X-Ray Imaging', price: 180 },
      { id: 'ortho_03', name: 'Joint Injection', price: 350 },
      { id: 'ortho_04', name: 'Physical Therapy Session', price: 120 },
      { id: 'ortho_05', name: 'Bone Density Test', price: 300 },
    ]
  },
  laboratory: {
    name: 'Laboratory',
    services: [
      { id: 'lab_01', name: 'Complete Blood Count', price: 50 },
      { id: 'lab_02', name: 'Blood Chemistry Panel', price: 80 },
      { id: 'lab_03', name: 'Urine Analysis', price: 40 },
      { id: 'lab_04', name: 'Lipid Profile', price: 70 },
      { id: 'lab_05', name: 'Thyroid Function Test', price: 90 },
    ]
  }
};

// Mock existing patients
const existingPatients = [
  { id: 'P-001', name: 'John Doe', phone: '(555) 123-4567', email: 'john.doe@email.com' },
  { id: 'P-002', name: 'Sarah Johnson', phone: '(555) 234-5678', email: 'sarah.j@email.com' },
  { id: 'P-003', name: 'Michael Brown', phone: '(555) 345-6789', email: 'mike.brown@email.com' },
  { id: 'P-004', name: 'Emily Wilson', phone: '(555) 456-7890', email: 'emily.w@email.com' },
  { id: 'P-005', name: 'David Garcia', phone: '(555) 567-8901', email: 'david.g@email.com' },
];

interface SelectedService {
  id: string;
  name: string;
  price: number;
  department: string;
  quantity: number;
}

interface InvoiceCreationDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export function InvoiceCreationDialog({ isOpen, onOpenChange }: InvoiceCreationDialogProps) {
  const [patientType, setPatientType] = useState<'existing' | 'new'>('existing');
  const [selectedPatient, setSelectedPatient] = useState('');
  const [newPatientData, setNewPatientData] = useState({
    name: '',
    phone: '',
    email: '',
    address: ''
  });
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([]);
  const [currentDepartment, setCurrentDepartment] = useState('');
  const [selectedServices, setSelectedServices] = useState<SelectedService[]>([]);
  const [paymentMethod, setPaymentMethod] = useState('');
  const [dueDate, setDueDate] = useState('');

  const handleAddDepartment = () => {
    if (currentDepartment && !selectedDepartments.includes(currentDepartment)) {
      setSelectedDepartments([...selectedDepartments, currentDepartment]);
      setCurrentDepartment('');
    }
  };

  const handleRemoveDepartment = (dept: string) => {
    setSelectedDepartments(selectedDepartments.filter(d => d !== dept));
    // Remove services from removed department
    setSelectedServices(selectedServices.filter(service => service.department !== dept));
  };

  const handleAddService = (departmentKey: string, service: any) => {
    const existingService = selectedServices.find(s => s.id === service.id);
    if (existingService) {
      // Increase quantity if service already exists
      setSelectedServices(selectedServices.map(s =>
        s.id === service.id ? { ...s, quantity: s.quantity + 1 } : s
      ));
    } else {
      // Add new service
      setSelectedServices([...selectedServices, {
        id: service.id,
        name: service.name,
        price: service.price,
        department: departmentServices[departmentKey as keyof typeof departmentServices].name,
        quantity: 1
      }]);
    }
  };

  const handleRemoveService = (serviceId: string) => {
    setSelectedServices(selectedServices.filter(service => service.id !== serviceId));
  };

  const handleUpdateQuantity = (serviceId: string, quantity: number) => {
    if (quantity <= 0) {
      handleRemoveService(serviceId);
    } else {
      setSelectedServices(selectedServices.map(service =>
        service.id === serviceId ? { ...service, quantity } : service
      ));
    }
  };

  const calculateTotal = () => {
    return selectedServices.reduce((total, service) => total + (service.price * service.quantity), 0);
  };

  const handleCreateInvoice = () => {
    // Here you would typically send the data to your backend
    console.log('Creating invoice...', {
      patientType,
      patient: patientType === 'existing' ? selectedPatient : newPatientData,
      services: selectedServices,
      total: calculateTotal(),
      paymentMethod,
      dueDate
    });

    // Reset form and close dialog
    setPatientType('existing');
    setSelectedPatient('');
    setNewPatientData({ name: '', phone: '', email: '', address: '' });
    setSelectedDepartments([]);
    setSelectedServices([]);
    setPaymentMethod('');
    setDueDate('');
    onOpenChange(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-teal-600" />
            Create New Invoice
          </DialogTitle>
          <DialogDescription>
            Generate a comprehensive billing invoice with multiple departments and services.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Patient & Department Selection */}
          <div className="space-y-6">
            {/* Patient Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <UserCheck className="h-5 w-5" />
                  Patient Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <RadioGroup value={patientType} onValueChange={(value: 'existing' | 'new') => setPatientType(value)}>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="existing" id="existing" />
                    <Label htmlFor="existing" className="flex items-center gap-2">
                      <UserCheck className="h-4 w-4" />
                      Existing Patient
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="new" id="new" />
                    <Label htmlFor="new" className="flex items-center gap-2">
                      <UserPlus className="h-4 w-4" />
                      New Patient
                    </Label>
                  </div>
                </RadioGroup>

                {patientType === 'existing' ? (
                  <div>
                    <Label htmlFor="patient-select">Select Patient</Label>
                    <Select value={selectedPatient} onValueChange={setSelectedPatient}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose an existing patient..." />
                      </SelectTrigger>
                      <SelectContent>
                        {existingPatients.map((patient) => (
                          <SelectItem key={patient.id} value={patient.id}>
                            <div className="flex flex-col">
                              <span>{patient.name}</span>
                              <span className="text-sm text-gray-500">{patient.id} • {patient.phone}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div>
                      <Label htmlFor="new-name">Full Name</Label>
                      <Input
                        id="new-name"
                        value={newPatientData.name}
                        onChange={(e) => setNewPatientData({...newPatientData, name: e.target.value})}
                        placeholder="Enter patient's full name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="new-phone">Phone Number</Label>
                      <Input
                        id="new-phone"
                        value={newPatientData.phone}
                        onChange={(e) => setNewPatientData({...newPatientData, phone: e.target.value})}
                        placeholder="(555) 123-4567"
                      />
                    </div>
                    <div>
                      <Label htmlFor="new-email">Email Address</Label>
                      <Input
                        id="new-email"
                        type="email"
                        value={newPatientData.email}
                        onChange={(e) => setNewPatientData({...newPatientData, email: e.target.value})}
                        placeholder="patient@email.com"
                      />
                    </div>
                    <div>
                      <Label htmlFor="new-address">Address</Label>
                      <Input
                        id="new-address"
                        value={newPatientData.address}
                        onChange={(e) => setNewPatientData({...newPatientData, address: e.target.value})}
                        placeholder="Patient's address"
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Department Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Department Services</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Select value={currentDepartment} onValueChange={setCurrentDepartment}>
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Select department..." />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(departmentServices).map(([key, dept]) => (
                        <SelectItem key={key} value={key}>{dept.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button onClick={handleAddDepartment} size="sm" className="bg-teal-600 hover:bg-teal-700">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>

                {selectedDepartments.length > 0 && (
                  <div className="space-y-2">
                    <Label>Selected Departments:</Label>
                    <div className="flex flex-wrap gap-2">
                      {selectedDepartments.map((deptKey) => (
                        <Badge key={deptKey} variant="secondary" className="flex items-center gap-1">
                          {departmentServices[deptKey as keyof typeof departmentServices].name}
                          <button
                            onClick={() => handleRemoveDepartment(deptKey)}
                            className="ml-1 hover:text-red-600"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Services for Selected Departments */}
                {selectedDepartments.map((deptKey) => (
                  <Card key={deptKey} className="border-gray-200">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">
                        {departmentServices[deptKey as keyof typeof departmentServices].name} Services
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 gap-2">
                        {departmentServices[deptKey as keyof typeof departmentServices].services.map((service) => (
                          <div key={service.id} className="flex items-center justify-between p-2 border rounded hover:bg-gray-50 dark:hover:bg-gray-700">
                            <div>
                              <p className="text-sm text-gray-900 dark:text-gray-100">{service.name}</p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">${service.price}</p>
                            </div>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleAddService(deptKey, service)}
                              className="text-teal-600 border-teal-600 hover:bg-teal-50"
                            >
                              <Plus className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Selected Services & Summary */}
          <div className="space-y-6">
            {/* Selected Services */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center justify-between">
                  Selected Services
                  <Badge variant="secondary">{selectedServices.length} items</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedServices.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <p>No services selected yet</p>
                    <p className="text-sm">Choose departments and add services to get started</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Service</TableHead>
                        <TableHead>Qty</TableHead>
                        <TableHead>Price</TableHead>
                        <TableHead>Total</TableHead>
                        <TableHead>Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedServices.map((service) => (
                        <TableRow key={service.id}>
                          <TableCell>
                            <div>
                              <p className="text-sm text-gray-900 dark:text-gray-100">{service.name}</p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">{service.department}</p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Input
                              type="number"
                              min="1"
                              value={service.quantity}
                              onChange={(e) => handleUpdateQuantity(service.id, parseInt(e.target.value) || 1)}
                              className="w-16 h-8"
                            />
                          </TableCell>
                          <TableCell className="text-gray-900 dark:text-gray-100">${service.price}</TableCell>
                          <TableCell className="text-gray-900 dark:text-gray-100">${service.price * service.quantity}</TableCell>
                          <TableCell>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleRemoveService(service.id)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            {/* Invoice Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Invoice Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between text-gray-900 dark:text-gray-100">
                    <span>Subtotal:</span>
                    <span>${calculateTotal().toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-gray-900 dark:text-gray-100">
                    <span>Tax (0%):</span>
                    <span>$0.00</span>
                  </div>
                  <div className="border-t pt-2">
                    <div className="flex justify-between text-lg">
                      <span className="text-gray-900 dark:text-gray-100">Total:</span>
                      <span className="text-teal-600 dark:text-teal-400">${calculateTotal().toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <Label htmlFor="payment-method">Payment Method</Label>
                    <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select payment method..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="card">Credit/Debit Card</SelectItem>
                        <SelectItem value="insurance">Insurance</SelectItem>
                        <SelectItem value="check">Check</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="due-date">Due Date</Label>
                    <Input
                      id="due-date"
                      type="date"
                      value={dueDate}
                      onChange={(e) => setDueDate(e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <Button
                onClick={handleCreateInvoice}
                className="flex-1 bg-teal-600 hover:bg-teal-700"
                disabled={selectedServices.length === 0 || (patientType === 'existing' ? !selectedPatient : !newPatientData.name)}
              >
                Create Invoice
              </Button>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
