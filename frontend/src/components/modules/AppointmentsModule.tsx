import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Calendar, Clock, User, Plus, Edit, Eye, Phone, Search, Filter, Check, X } from 'lucide-react';

import { appointmentsData, appointmentStatuses, dateFilters } from './data/appointmentsData';
import { getStatusBadge, getPriorityBadge, getTypeIcon, filterAppointments, getAppointmentStats } from './utils/appointmentUtils';
import { AppointmentDetailsDialog } from './components/AppointmentDetailsDialog';
import { AppointmentScheduleDialog } from './components/AppointmentScheduleDialog';

export function AppointmentsModule() {
  const [selectedAppointment, setSelectedAppointment] = useState<any>(null);
  const [isAppointmentDetailsOpen, setIsAppointmentDetailsOpen] = useState(false);
  const [isScheduleAppointmentOpen, setIsScheduleAppointmentOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterDate, setFilterDate] = useState('today');
  const [searchTerm, setSearchTerm] = useState('');
  const [newAppointment, setNewAppointment] = useState({
    patientName: '',
    patientId: '',
    doctorName: '',
    department: '',
    date: '',
    time: '',
    type: '',
    reason: '',
    priority: 'Normal'
  });

  const filteredAppointments = filterAppointments(appointmentsData, filterStatus, searchTerm);
  const stats = getAppointmentStats(appointmentsData);

  const handleViewDetails = (appointment: any) => {
    setSelectedAppointment(appointment);
    setIsAppointmentDetailsOpen(true);
  };

  const handleScheduleAppointment = () => {
    console.log('Scheduling appointment:', newAppointment);
    setIsScheduleAppointmentOpen(false);
    setNewAppointment({
      patientName: '',
      patientId: '',
      doctorName: '',
      department: '',
      date: '',
      time: '',
      type: '',
      reason: '',
      priority: 'Normal'
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl text-gray-900">Appointment Management</h2>
          <p className="text-gray-600">Schedule, track, and manage patient appointments</p>
        </div>
        <AppointmentScheduleDialog
          isOpen={isScheduleAppointmentOpen}
          onOpenChange={setIsScheduleAppointmentOpen}
          newAppointment={newAppointment}
          setNewAppointment={setNewAppointment}
          onSchedule={handleScheduleAppointment}
        />
      </div>

      {/* Appointment Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Today's Appointments</p>
                <p className="text-2xl text-gray-900">{stats.total}</p>
                <p className="text-sm text-blue-600">Total scheduled</p>
              </div>
              <Calendar className="h-8 w-8 text-teal-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl text-gray-900">{stats.completed}</p>
                <p className="text-sm text-green-600">Successful visits</p>
              </div>
              <Check className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">In Progress</p>
                <p className="text-2xl text-gray-900">{stats.inProgress}</p>
                <p className="text-sm text-orange-600">Currently active</p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">No Shows</p>
                <p className="text-2xl text-gray-900">{stats.noShows}</p>
                <p className="text-sm text-red-600">Missed appointments</p>
              </div>
              <X className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Search & Filter Appointments</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by patient name, appointment ID, or doctor..."
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
                  {appointmentStatuses.slice(1).map(status => (
                    <SelectItem key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={filterDate} onValueChange={setFilterDate}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {dateFilters.map(filter => (
                    <SelectItem key={filter.value} value={filter.value}>
                      {filter.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Appointments Table */}
      <Card>
        <CardHeader>
          <CardTitle>Appointment Schedule ({filteredAppointments.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Appointment</TableHead>
                <TableHead>Patient</TableHead>
                <TableHead>Doctor</TableHead>
                <TableHead>Time</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAppointments.map((appointment) => (
                <TableRow key={appointment.id}>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{appointment.id}</p>
                      <p className="text-sm text-gray-500">{appointment.reason}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{appointment.patientName}</p>
                      <p className="text-sm text-gray-500">{appointment.patientId}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="text-gray-900">{appointment.doctorName}</p>
                      <p className="text-sm text-gray-500">{appointment.department}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-600">{new Date(appointment.date).toLocaleDateString()}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-600">{appointment.time} ({appointment.duration})</span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      {getTypeIcon(appointment.type)}
                      <span className="text-sm">{appointment.type}</span>
                    </div>
                  </TableCell>
                  <TableCell>{getPriorityBadge(appointment.priority)}</TableCell>
                  <TableCell>{getStatusBadge(appointment.status)}</TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button variant="ghost" size="sm" onClick={() => handleViewDetails(appointment)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Phone className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <AppointmentDetailsDialog
        isOpen={isAppointmentDetailsOpen}
        onOpenChange={setIsAppointmentDetailsOpen}
        appointment={selectedAppointment}
      />
    </div>
  );
}
