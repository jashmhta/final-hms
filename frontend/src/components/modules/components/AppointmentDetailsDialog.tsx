import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Label } from '../../ui/label';
import { Edit, Phone, Calendar, X } from 'lucide-react';
import { getStatusBadge, getPriorityBadge } from '../utils/appointmentUtils';

interface AppointmentDetailsDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  appointment: any;
}

export function AppointmentDetailsDialog({
  isOpen,
  onOpenChange,
  appointment
}: AppointmentDetailsDialogProps) {
  if (!appointment) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{appointment.id} - Appointment Details</DialogTitle>
          <DialogDescription>
            Comprehensive appointment information and patient details.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Appointment Information */}
          <div>
            <h3 className="text-lg text-gray-900 mb-3">Appointment Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Appointment ID</Label>
                <p className="text-gray-900">{appointment.id}</p>
              </div>
              <div>
                <Label>Type</Label>
                <p className="text-gray-900">{appointment.type}</p>
              </div>
              <div>
                <Label>Date & Time</Label>
                <p className="text-gray-900">{new Date(appointment.date).toLocaleDateString()} at {appointment.time}</p>
              </div>
              <div>
                <Label>Duration</Label>
                <p className="text-gray-900">{appointment.duration}</p>
              </div>
              <div>
                <Label>Priority</Label>
                <div className="mt-1">{getPriorityBadge(appointment.priority)}</div>
              </div>
              <div>
                <Label>Status</Label>
                <div className="mt-1">{getStatusBadge(appointment.status)}</div>
              </div>
            </div>
          </div>

          {/* Patient Information */}
          <div>
            <h3 className="text-lg text-gray-900 mb-3">Patient Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Patient Name</Label>
                <p className="text-gray-900">{appointment.patientName}</p>
              </div>
              <div>
                <Label>Patient ID</Label>
                <p className="text-gray-900">{appointment.patientId}</p>
              </div>
              <div>
                <Label>Phone Number</Label>
                <p className="text-gray-900">{appointment.phone}</p>
              </div>
              <div>
                <Label>Reason for Visit</Label>
                <p className="text-gray-900">{appointment.reason}</p>
              </div>
            </div>
          </div>

          {/* Medical Staff Information */}
          <div>
            <h3 className="text-lg text-gray-900 mb-3">Medical Staff Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Assigned Doctor</Label>
                <p className="text-gray-900">{appointment.doctorName}</p>
              </div>
              <div>
                <Label>Department</Label>
                <p className="text-gray-900">{appointment.department}</p>
              </div>
            </div>
          </div>

          {/* Notes */}
          <div>
            <h3 className="text-lg text-gray-900 mb-3">Notes</h3>
            <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{appointment.notes}</p>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-2">
            <Button className="bg-teal-600 hover:bg-teal-700">
              <Edit className="h-4 w-4 mr-2" />
              Edit Appointment
            </Button>
            <Button variant="outline">
              <Phone className="h-4 w-4 mr-2" />
              Call Patient
            </Button>
            <Button variant="outline">
              <Calendar className="h-4 w-4 mr-2" />
              Reschedule
            </Button>
            {appointment.status === 'Scheduled' && (
              <Button variant="outline" className="text-red-600 hover:text-red-700">
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
