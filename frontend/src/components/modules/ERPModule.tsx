import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import {
  Building2,
  Users,
  DollarSign,
  Package,
  Truck,
  FileText,
  Calendar,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Plus,
  Search,
  Download,
  BarChart3,
  PieChart,
  Activity,
  Zap
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Cell, LineChart, Line, Area, AreaChart, Pie } from 'recharts';

// Mock data for ERP components
const departmentPerformance = [
  { name: 'Cardiology', revenue: 450000, patients: 450, efficiency: 95 },
  { name: 'Emergency', revenue: 380000, patients: 1200, efficiency: 88 },
  { name: 'Pediatrics', revenue: 320000, patients: 680, efficiency: 92 },
  { name: 'Orthopedics', revenue: 290000, patients: 380, efficiency: 91 },
  { name: 'Neurology', revenue: 480000, patients: 320, efficiency: 94 },
  { name: 'Oncology', revenue: 520000, patients: 280, efficiency: 96 }
];

const resourceUtilization = [
  { name: 'Jan', beds: 85, equipment: 78, staff: 92 },
  { name: 'Feb', beds: 88, equipment: 82, staff: 89 },
  { name: 'Mar', beds: 82, equipment: 85, staff: 91 },
  { name: 'Apr', beds: 90, equipment: 88, staff: 94 },
  { name: 'May', beds: 87, equipment: 83, staff: 88 },
  { name: 'Jun', beds: 93, equipment: 90, staff: 96 }
];

const expenseBreakdown = [
  { name: 'Staff Salaries', value: 45, amount: 2250000 },
  { name: 'Medical Supplies', value: 22, amount: 1100000 },
  { name: 'Equipment', value: 15, amount: 750000 },
  { name: 'Utilities', value: 8, amount: 400000 },
  { name: 'Maintenance', value: 6, amount: 300000 },
  { name: 'Other', value: 4, amount: 200000 }
];

const COLORS = ['#0891b2', '#0d9488', '#059669', '#10b981', '#34d399', '#6ee7b7'];

const vendors = [
  { id: 'V001', name: 'MedSupply Corp', category: 'Medical Supplies', rating: 4.8, totalOrders: 145, status: 'Active' },
  { id: 'V002', name: 'TechHealth Solutions', category: 'Equipment', rating: 4.9, totalOrders: 89, status: 'Active' },
  { id: 'V003', name: 'PharmaCare Ltd', category: 'Pharmaceuticals', rating: 4.7, totalOrders: 267, status: 'Active' },
  { id: 'V004', name: 'CleanCare Services', category: 'Maintenance', rating: 4.5, totalOrders: 56, status: 'Pending' }
];

const purchaseOrders = [
  { id: 'PO-2024-001', vendor: 'MedSupply Corp', amount: 25000, items: 12, status: 'Delivered', date: '2024-01-15' },
  { id: 'PO-2024-002', vendor: 'TechHealth Solutions', amount: 120000, items: 3, status: 'In Transit', date: '2024-01-18' },
  { id: 'PO-2024-003', vendor: 'PharmaCare Ltd', amount: 45000, items: 25, status: 'Processing', date: '2024-01-20' },
  { id: 'PO-2024-004', vendor: 'CleanCare Services', amount: 8000, items: 8, status: 'Pending', date: '2024-01-22' }
];

const assets = [
  { id: 'EQ-001', name: 'MRI Scanner', category: 'Imaging', location: 'Radiology Wing', value: 2500000, status: 'Operational', lastMaintenance: '2024-01-10' },
  { id: 'EQ-002', name: 'CT Scanner', category: 'Imaging', location: 'Emergency Dept', value: 1800000, status: 'Maintenance', lastMaintenance: '2024-01-05' },
  { id: 'EQ-003', name: 'Ultrasound Machine', category: 'Imaging', location: 'OPD Wing', value: 450000, status: 'Operational', lastMaintenance: '2024-01-12' },
  { id: 'EQ-004', name: 'Ventilator Unit', category: 'Critical Care', location: 'ICU', value: 850000, status: 'Operational', lastMaintenance: '2024-01-08' }
];

export function ERPModule() {
  const [isAddVendorOpen, setIsAddVendorOpen] = useState(false);
  const [isAddPOOpen, setIsAddPOOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl text-gray-900">Enterprise Resource Planning (ERP)</h1>
        <p className="text-gray-600">Comprehensive business process management and resource optimization</p>
      </div>

      {/* Key Metrics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Revenue</p>
                <p className="text-2xl text-gray-900">₹24.8M</p>
                <p className="text-xs text-green-600 flex items-center mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  +12.5% from last month
                </p>
              </div>
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Operational Efficiency</p>
                <p className="text-2xl text-gray-900">92.8%</p>
                <p className="text-xs text-blue-600 flex items-center mt-1">
                  <Activity className="h-3 w-3 mr-1" />
                  Above target (90%)
                </p>
              </div>
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <BarChart3 className="h-5 w-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Vendors</p>
                <p className="text-2xl text-gray-900">47</p>
                <p className="text-xs text-teal-600 flex items-center mt-1">
                  <Building2 className="h-3 w-3 mr-1" />
                  3 new this month
                </p>
              </div>
              <div className="w-10 h-10 bg-teal-100 rounded-lg flex items-center justify-center">
                <Truck className="h-5 w-5 text-teal-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Asset Value</p>
                <p className="text-2xl text-gray-900">₹18.5M</p>
                <p className="text-xs text-purple-600 flex items-center mt-1">
                  <Package className="h-3 w-3 mr-1" />
                  247 assets tracked
                </p>
              </div>
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <Package className="h-5 w-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ERP Module Tabs */}
      <Tabs defaultValue="analytics" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="procurement">Procurement</TabsTrigger>
          <TabsTrigger value="assets">Asset Management</TabsTrigger>
          <TabsTrigger value="finance">Financial Control</TabsTrigger>
          <TabsTrigger value="planning">Strategic Planning</TabsTrigger>
        </TabsList>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Department Performance */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-teal-600" />
                  <span>Department Performance</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={departmentPerformance}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="revenue" fill="#0891b2" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Resource Utilization */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-blue-600" />
                  <span>Resource Utilization Trends</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={resourceUtilization}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="beds" stackId="1" stroke="#0891b2" fill="#0891b2" />
                    <Area type="monotone" dataKey="equipment" stackId="1" stroke="#0d9488" fill="#0d9488" />
                    <Area type="monotone" dataKey="staff" stackId="1" stroke="#059669" fill="#059669" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Expense Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <PieChart className="h-5 w-5 text-green-600" />
                <span>Operational Expense Breakdown</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      data={expenseBreakdown}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {expenseBreakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPieChart>
                </ResponsiveContainer>
                <div className="space-y-3">
                  {expenseBreakdown.map((item, index) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span className="text-sm text-gray-700">{item.name}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-900">₹{(item.amount / 100000).toFixed(1)}L</p>
                        <p className="text-xs text-gray-500">{item.value}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Procurement Tab */}
        <TabsContent value="procurement" className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg text-gray-900">Vendor & Procurement Management</h3>
            <div className="flex space-x-2">
              <Dialog open={isAddVendorOpen} onOpenChange={setIsAddVendorOpen}>
                <DialogTrigger asChild>
                  <Button size="sm" className="bg-teal-600 hover:bg-teal-700">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Vendor
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Vendor</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label>Vendor Name</Label>
                      <Input placeholder="Enter vendor name" />
                    </div>
                    <div>
                      <Label>Category</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="medical">Medical Supplies</SelectItem>
                          <SelectItem value="equipment">Equipment</SelectItem>
                          <SelectItem value="pharmaceuticals">Pharmaceuticals</SelectItem>
                          <SelectItem value="maintenance">Maintenance</SelectItem>
                          <SelectItem value="food">Food Services</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Contact Information</Label>
                      <Input placeholder="Email address" />
                    </div>
                    <div>
                      <Label>Notes</Label>
                      <Textarea placeholder="Additional vendor information" />
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" onClick={() => setIsAddVendorOpen(false)}>Cancel</Button>
                      <Button className="bg-teal-600 hover:bg-teal-700">Add Vendor</Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>

              <Dialog open={isAddPOOpen} onOpenChange={setIsAddPOOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    New Purchase Order
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Create Purchase Order</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label>Vendor</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Select vendor" />
                        </SelectTrigger>
                        <SelectContent>
                          {vendors.map(vendor => (
                            <SelectItem key={vendor.id} value={vendor.id}>{vendor.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Expected Amount</Label>
                      <Input type="number" placeholder="Enter amount" />
                    </div>
                    <div>
                      <Label>Delivery Date</Label>
                      <Input type="date" />
                    </div>
                    <div>
                      <Label>Items Description</Label>
                      <Textarea placeholder="List items to be ordered" />
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" onClick={() => setIsAddPOOpen(false)}>Cancel</Button>
                      <Button className="bg-teal-600 hover:bg-teal-700">Create Order</Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Vendors List */}
            <Card>
              <CardHeader>
                <CardTitle>Active Vendors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {vendors.map(vendor => (
                    <div key={vendor.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                      <div>
                        <h4 className="text-sm text-gray-900">{vendor.name}</h4>
                        <p className="text-xs text-gray-600">{vendor.category}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-yellow-400 rounded-full mr-1"></div>
                            <span className="text-xs text-gray-500">{vendor.rating}/5</span>
                          </div>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500">{vendor.totalOrders} orders</span>
                        </div>
                      </div>
                      <Badge variant={vendor.status === 'Active' ? 'default' : 'secondary'}>
                        {vendor.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Purchase Orders */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Purchase Orders</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {purchaseOrders.map(order => (
                    <div key={order.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                      <div>
                        <h4 className="text-sm text-gray-900">{order.id}</h4>
                        <p className="text-xs text-gray-600">{order.vendor}</p>
                        <p className="text-xs text-gray-500">₹{order.amount.toLocaleString()} • {order.items} items</p>
                      </div>
                      <div className="text-right">
                        <Badge
                          variant={order.status === 'Delivered' ? 'default' :
                                 order.status === 'In Transit' ? 'secondary' : 'outline'}
                        >
                          {order.status}
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">{order.date}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Asset Management Tab */}
        <TabsContent value="assets" className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg text-gray-900">Hospital Asset Management</h3>
            <div className="flex space-x-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search assets..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs text-gray-500 uppercase tracking-wider">Asset</th>
                      <th className="px-6 py-3 text-left text-xs text-gray-500 uppercase tracking-wider">Category</th>
                      <th className="px-6 py-3 text-left text-xs text-gray-500 uppercase tracking-wider">Location</th>
                      <th className="px-6 py-3 text-left text-xs text-gray-500 uppercase tracking-wider">Value</th>
                      <th className="px-6 py-3 text-left text-xs text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs text-gray-500 uppercase tracking-wider">Last Maintenance</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {assets.map(asset => (
                      <tr key={asset.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <p className="text-sm text-gray-900">{asset.name}</p>
                            <p className="text-xs text-gray-500">{asset.id}</p>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {asset.category}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {asset.location}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          ₹{(asset.value / 100000).toFixed(1)}L
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge
                            variant={asset.status === 'Operational' ? 'default' : 'secondary'}
                            className={asset.status === 'Operational' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}
                          >
                            {asset.status}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {asset.lastMaintenance}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Financial Control Tab */}
        <TabsContent value="finance" className="space-y-6">
          <h3 className="text-lg text-gray-900">Financial Management & Control</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Monthly Budget</p>
                    <p className="text-xl text-gray-900">₹5.2M</p>
                    <p className="text-xs text-green-600">₹1.8M remaining</p>
                  </div>
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <DollarSign className="h-4 w-4 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Outstanding Invoices</p>
                    <p className="text-xl text-gray-900">₹850K</p>
                    <p className="text-xs text-orange-600">23 pending</p>
                  </div>
                  <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                    <Clock className="h-4 w-4 text-orange-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Cost per Patient</p>
                    <p className="text-xl text-gray-900">₹3,245</p>
                    <p className="text-xs text-blue-600">-5% vs last month</p>
                  </div>
                  <div className="w-8 h-8 bg-teal-100 rounded-lg flex items-center justify-center">
                    <Users className="h-4 w-4 text-teal-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Budget vs Actual Spending</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">This feature provides detailed financial tracking and budget management tools for hospital operations.</p>
              <div className="bg-gray-50 p-6 rounded-lg text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <h4 className="text-lg text-gray-900 mb-2">Advanced Financial Analytics</h4>
                <p className="text-sm text-gray-600 mb-4">Comprehensive budget tracking, variance analysis, and financial forecasting tools.</p>
                <Button variant="outline" size="sm">
                  Configure Financial Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Strategic Planning Tab */}
        <TabsContent value="planning" className="space-y-6">
          <h3 className="text-lg text-gray-900">Strategic Planning & Forecasting</h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="h-5 w-5 text-purple-600" />
                  <span>Key Performance Indicators</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-700">Patient Satisfaction</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="w-4/5 bg-green-500 h-2 rounded-full"></div>
                      </div>
                      <span className="text-sm text-gray-900">4.2/5</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-700">Operational Efficiency</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="w-5/6 bg-blue-500 h-2 rounded-full"></div>
                      </div>
                      <span className="text-sm text-gray-900">92%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-700">Cost Optimization</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="w-3/4 bg-teal-500 h-2 rounded-full"></div>
                      </div>
                      <span className="text-sm text-gray-900">88%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-700">Quality Metrics</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="w-full bg-green-500 h-2 rounded-full"></div>
                      </div>
                      <span className="text-sm text-gray-900">95%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Calendar className="h-5 w-5 text-indigo-600" />
                  <span>Strategic Initiatives</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm text-gray-900">Digital Transformation</h4>
                      <Badge className="bg-blue-100 text-blue-800">In Progress</Badge>
                    </div>
                    <p className="text-xs text-gray-600">Implementing AI-powered patient management system</p>
                    <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                      <div className="w-3/5 bg-blue-500 h-1 rounded-full"></div>
                    </div>
                  </div>
                  <div className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm text-gray-900">Capacity Expansion</h4>
                      <Badge className="bg-green-100 text-green-800">Planning</Badge>
                    </div>
                    <p className="text-xs text-gray-600">New wing construction for 100 additional beds</p>
                    <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                      <div className="w-1/4 bg-green-500 h-1 rounded-full"></div>
                    </div>
                  </div>
                  <div className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm text-gray-900">Quality Certification</h4>
                      <Badge className="bg-orange-100 text-orange-800">Review</Badge>
                    </div>
                    <p className="text-xs text-gray-600">NABH accreditation renewal process</p>
                    <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                      <div className="w-5/6 bg-orange-500 h-1 rounded-full"></div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Business Intelligence Dashboard</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">Advanced analytics and predictive modeling for strategic decision making.</p>
              <div className="bg-gradient-to-r from-teal-50 to-blue-50 p-6 rounded-lg text-center">
                <Activity className="h-12 w-12 text-teal-600 mx-auto mb-3" />
                <h4 className="text-lg text-gray-900 mb-2">Predictive Analytics Engine</h4>
                <p className="text-sm text-gray-600 mb-4">Machine learning powered insights for resource planning, patient flow optimization, and revenue forecasting.</p>
                <Button className="bg-teal-600 hover:bg-teal-700">
                  Access BI Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
