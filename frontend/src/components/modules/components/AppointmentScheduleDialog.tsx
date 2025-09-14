import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Plus } from 'lucide-react';
import { doctors, departments, appointmentTypes, priorityLevels } from '../data/appointmentsData';

interface AppointmentScheduleDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  newAppointment: any;
  setNewAppointment: (appointment: any) => void;
  onSchedule: () => void;
}

export function AppointmentScheduleDialog({
  isOpen,
  onOpenChange,
  newAppointment,
  setNewAppointment,
  onSchedule
}: AppointmentScheduleDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button className="bg-teal-600 hover:bg-teal-700">
          <Plus className="h-4 w-4 mr-2" />
          Schedule Appointment
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Schedule New Appointment</DialogTitle>
          <DialogDescription>
            Book a new appointment for a patient with available doctors.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="patientName">Patient Name</Label>
              <Input
                id="patientName"
                value={newAppointment.patientName}
                onChange={(e) => setNewAppointment({ ...newAppointment, patientName: e.target.value })}
                placeholder="John Doe"
              />
            </div>
            <div>
              <Label htmlFor="patientId">Patient ID</Label>
              <Input
                id="patientId"
                value={newAppointment.patientId}
                onChange={(e) => setNewAppointment({ ...newAppointment, patientId: e.target.value })}
                placeholder="P-001"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="department">Department</Label>
              <Select value={newAppointment.department} onValueChange={(value) => setNewAppointment({ ...newAppointment, department: value })}>
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
              <Label htmlFor="doctorName">Doctor</Label>
              <Select value={newAppointment.doctorName} onValueChange={(value) => setNewAppointment({ ...newAppointment, doctorName: value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select doctor" />
                </SelectTrigger>
                <SelectContent>
                  {doctors.map(doctor => (
                    <SelectItem key={doctor} value={doctor}>{doctor}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="date">Date</Label>
              <Input
                id="date"
                type="date"
                value={newAppointment.date}
                onChange={(e) => setNewAppointment({ ...newAppointment, date: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="time">Time</Label>
              <Input
                id="time"
                type="time"
                value={newAppointment.time}
                onChange={(e) => setNewAppointment({ ...newAppointment, time: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="type">Type</Label>
              <Select value={newAppointment.type} onValueChange={(value) => setNewAppointment({ ...newAppointment, type: value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {appointmentTypes.map(type => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="reason">Reason for Visit</Label>
              <Input
                id="reason"
                value={newAppointment.reason}
                onChange={(e) => setNewAppointment({ ...newAppointment, reason: e.target.value })}
                placeholder="Reason for appointment"
              />
            </div>
            <div>
              <Label htmlFor="priority">Priority</Label>
              <Select value={newAppointment.priority} onValueChange={(value) => setNewAppointment({ ...newAppointment, priority: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {priorityLevels.map(priority => (
                    <SelectItem key={priority} value={priority}>{priority}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex space-x-2 pt-4">
            <Button onClick={onSchedule} className="bg-teal-600 hover:bg-teal-700">
              Schedule Appointment
            </Button>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
