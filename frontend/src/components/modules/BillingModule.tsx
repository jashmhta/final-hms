import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { CreditCard, DollarSign, FileText, Plus, Eye, Edit, Download, Search, Filter, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { InvoiceCreationDialog } from './components/InvoiceCreationDialog';

const billingData = [
  {
    id: 'INV-001',
    patientName: 'John Doe',
    patientId: 'P-001',
    amount: 1250.00,
    services: ['Cardiology Consultation', 'ECG Test'],
    date: '2024-01-28',
    dueDate: '2024-02-28',
    status: 'Paid',
    paymentMethod: 'Insurance',
    insuranceProvider: 'BlueCross BlueShield',
    doctor: 'Dr. James Smith',
    department: 'Cardiology'
  },
  {
    id: 'INV-002',
    patientName: 'Sarah Johnson',
    patientId: 'P-002',
    amount: 750.00,
    services: ['Pediatric Check-up', 'Vaccination'],
    date: '2024-01-28',
    dueDate: '2024-02-28',
    status: 'Pending',
    paymentMethod: 'Cash',
    insuranceProvider: 'Aetna',
    doctor: 'Dr. Sarah Williams',
    department: 'Pediatrics'
  },
  {
    id: 'INV-003',
    patientName: 'Michael Brown',
    patientId: 'P-003',
    amount: 2850.00,
    services: ['Emergency Care', 'CT Scan', 'Blood Tests'],
    date: '2024-01-27',
    dueDate: '2024-02-27',
    status: 'Overdue',
    paymentMethod: 'Insurance',
    insuranceProvider: 'Medicare',
    doctor: 'Dr. Michael Davis',
    department: 'Emergency'
  },
  {
    id: 'INV-004',
    patientName: 'Emily Wilson',
    patientId: 'P-004',
    amount: 950.00,
    services: ['Neurology Consultation', 'MRI Scan'],
    date: '2024-01-26',
    dueDate: '2024-02-26',
    status: 'Partially Paid',
    paymentMethod: 'Credit Card',
    insuranceProvider: 'United Healthcare',
    doctor: 'Dr. Emily Lee',
    department: 'Neurology'
  }
];

export function BillingModule() {
  const [selectedBill, setSelectedBill] = useState<any>(null);
  const [isBillDetailsOpen, setIsBillDetailsOpen] = useState(false);
  const [isNewBillOpen, setIsNewBillOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredBills = billingData.filter(bill => {
    const statusMatch = filterStatus === 'all' || bill.status.toLowerCase() === filterStatus.toLowerCase();
    const searchMatch = bill.patientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       bill.id.toLowerCase().includes(searchTerm.toLowerCase());
    return statusMatch && searchMatch;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Paid':
        return <Badge className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">Paid</Badge>;
      case 'Pending':
        return <Badge className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">Pending</Badge>;
      case 'Overdue':
        return <Badge className="bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">Overdue</Badge>;
      case 'Partially Paid':
        return <Badge className="bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200">Partially Paid</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const totalRevenue = billingData.reduce((sum, bill) => sum + bill.amount, 0);
  const paidAmount = billingData.filter(b => b.status === 'Paid').reduce((sum, bill) => sum + bill.amount, 0);
  const pendingAmount = billingData.filter(b => b.status === 'Pending').reduce((sum, bill) => sum + bill.amount, 0);
  const overdueAmount = billingData.filter(b => b.status === 'Overdue').reduce((sum, bill) => sum + bill.amount, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl text-gray-900 dark:text-gray-100">Billing & Finance</h2>
          <p className="text-gray-600 dark:text-gray-400">Manage invoices, payments, and financial records</p>
        </div>
        <Button
          onClick={() => setIsNewBillOpen(true)}
          className="bg-teal-600 hover:bg-teal-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Invoice
        </Button>
      </div>

      {/* Financial Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Revenue</p>
                <p className="text-2xl text-gray-900 dark:text-gray-100">${totalRevenue.toLocaleString()}</p>
                <p className="text-sm text-blue-600">This month</p>
              </div>
              <DollarSign className="h-8 w-8 text-teal-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Paid Amount</p>
                <p className="text-2xl text-gray-900 dark:text-gray-100">${paidAmount.toLocaleString()}</p>
                <p className="text-sm text-green-600">Collected</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Pending</p>
                <p className="text-2xl text-gray-900 dark:text-gray-100">${pendingAmount.toLocaleString()}</p>
                <p className="text-sm text-orange-600">Awaiting payment</p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Overdue</p>
                <p className="text-2xl text-gray-900 dark:text-gray-100">${overdueAmount.toLocaleString()}</p>
                <p className="text-sm text-red-600">Past due date</p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Search & Filter Invoices</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by patient name or invoice ID..."
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
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="overdue">Overdue</SelectItem>
                  <SelectItem value="partially paid">Partially Paid</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Billing Table */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice Management ({filteredBills.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice ID</TableHead>
                <TableHead>Patient</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Services</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredBills.map((bill) => (
                <TableRow key={bill.id}>
                  <TableCell className="text-gray-900 dark:text-gray-100">{bill.id}</TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900 dark:text-gray-100">{bill.patientName}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{bill.patientId}</p>
                    </div>
                  </TableCell>
                  <TableCell className="text-gray-900 dark:text-gray-100">${bill.amount.toLocaleString()}</TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      {bill.services.map((service, index) => (
                        <div key={index} className="text-xs text-gray-600 dark:text-gray-400">{service}</div>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900 dark:text-gray-100">{new Date(bill.date).toLocaleDateString()}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Due: {new Date(bill.dueDate).toLocaleDateString()}</p>
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(bill.status)}</TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button variant="ghost" size="sm" onClick={() => {
                        setSelectedBill(bill);
                        setIsBillDetailsOpen(true);
                      }}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Bill Details Dialog */}
      <Dialog open={isBillDetailsOpen} onOpenChange={setIsBillDetailsOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedBill?.id} - Invoice Details</DialogTitle>
            <DialogDescription>Comprehensive billing information and payment details.</DialogDescription>
          </DialogHeader>
          {selectedBill && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Invoice ID</Label>
                  <p className="text-gray-900 dark:text-gray-100">{selectedBill.id}</p>
                </div>
                <div>
                  <Label>Patient</Label>
                  <p className="text-gray-900 dark:text-gray-100">{selectedBill.patientName} ({selectedBill.patientId})</p>
                </div>
                <div>
                  <Label>Amount</Label>
                  <p className="text-gray-900 dark:text-gray-100">${selectedBill.amount.toLocaleString()}</p>
                </div>
                <div>
                  <Label>Status</Label>
                  <div className="mt-1">{getStatusBadge(selectedBill.status)}</div>
                </div>
                <div>
                  <Label>Doctor</Label>
                  <p className="text-gray-900 dark:text-gray-100">{selectedBill.doctor}</p>
                </div>
                <div>
                  <Label>Department</Label>
                  <p className="text-gray-900 dark:text-gray-100">{selectedBill.department}</p>
                </div>
              </div>
              <div>
                <Label>Services</Label>
                <div className="mt-2 space-y-1">
                  {selectedBill.services.map((service: string, index: number) => (
                    <p key={index} className="text-gray-900 dark:text-gray-100">• {service}</p>
                  ))}
                </div>
              </div>
              <div className="flex space-x-2 pt-4">
                <Button className="bg-teal-600 hover:bg-teal-700">
                  <CreditCard className="h-4 w-4 mr-2" />
                  Process Payment
                </Button>
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Download PDF
                </Button>
                <Button variant="outline">
                  <FileText className="h-4 w-4 mr-2" />
                  Send Invoice
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Enhanced Invoice Creation Dialog */}
      <InvoiceCreationDialog
        isOpen={isNewBillOpen}
        onOpenChange={setIsNewBillOpen}
      />
    </div>
  );
}
