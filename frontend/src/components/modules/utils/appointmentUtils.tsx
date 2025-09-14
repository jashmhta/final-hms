import { Badge } from '../../ui/badge';
import { AlertCircle, Clock, User, UserCheck } from 'lucide-react';

export const getStatusBadge = (status: string) => {
  switch (status) {
    case 'Scheduled':
      return <Badge className="bg-blue-100 text-blue-800">Scheduled</Badge>;
    case 'In Progress':
      return <Badge className="bg-orange-100 text-orange-800">In Progress</Badge>;
    case 'Completed':
      return <Badge className="bg-green-100 text-green-800">Completed</Badge>;
    case 'Cancelled':
      return <Badge className="bg-red-100 text-red-800">Cancelled</Badge>;
    case 'No Show':
      return <Badge className="bg-gray-100 text-gray-800">No Show</Badge>;
    default:
      return <Badge>{status}</Badge>;
  }
};

export const getPriorityBadge = (priority: string) => {
  switch (priority) {
    case 'High':
      return <Badge className="bg-red-100 text-red-800">High</Badge>;
    case 'Normal':
      return <Badge className="bg-blue-100 text-blue-800">Normal</Badge>;
    case 'Low':
      return <Badge className="bg-gray-100 text-gray-800">Low</Badge>;
    default:
      return <Badge>{priority}</Badge>;
  }
};

export const getTypeIcon = (type: string) => {
  switch (type) {
    case 'Emergency':
      return <AlertCircle className="h-4 w-4 text-red-600" />;
    case 'Surgery':
      return <UserCheck className="h-4 w-4 text-purple-600" />;
    case 'Follow-up':
      return <Clock className="h-4 w-4 text-orange-600" />;
    default:
      return <User className="h-4 w-4 text-blue-600" />;
  }
};

export const filterAppointments = (appointments: any[], statusFilter: string, searchTerm: string) => {
  return appointments.filter(appointment => {
    const statusMatch = statusFilter === 'all' || appointment.status.toLowerCase() === statusFilter.toLowerCase();
    const searchMatch = appointment.patientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       appointment.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       appointment.doctorName.toLowerCase().includes(searchTerm.toLowerCase());
    return statusMatch && searchMatch;
  });
};

export const getAppointmentStats = (appointments: any[]) => {
  return {
    total: appointments.length,
    completed: appointments.filter(a => a.status === 'Completed').length,
    inProgress: appointments.filter(a => a.status === 'In Progress').length,
    noShows: appointments.filter(a => a.status === 'No Show').length
  };
};
