export const appointmentsData = [
  {
    id: 'APT-001',
    patientName: 'John Doe',
    patientId: 'P-001',
    doctorName: 'Dr. James Smith',
    department: 'Cardiology',
    date: '2024-01-28',
    time: '09:00 AM',
    duration: '30 mins',
    type: 'Consultation',
    status: 'Scheduled',
    priority: 'Normal',
    reason: 'Chest pain follow-up',
    phone: '+1-555-0123',
    notes: 'Regular follow-up for cardiac condition'
  },
  {
    id: 'APT-002',
    patientName: 'Sarah Johnson',
    patientId: 'P-002',
    doctorName: 'Dr. Sarah Williams',
    department: 'Pediatrics',
    date: '2024-01-28',
    time: '10:30 AM',
    duration: '45 mins',
    type: 'Check-up',
    status: 'In Progress',
    priority: 'Normal',
    reason: 'Routine pediatric check-up',
    phone: '+1-555-0125',
    notes: 'Annual wellness visit for child'
  },
  {
    id: 'APT-003',
    patientName: 'Michael Brown',
    patientId: 'P-003',
    doctorName: 'Dr. Michael Davis',
    department: 'Emergency',
    date: '2024-01-28',
    time: '11:00 AM',
    duration: '60 mins',
    type: 'Emergency',
    status: 'Completed',
    priority: 'High',
    reason: 'Severe abdominal pain',
    phone: '+1-555-0127',
    notes: 'Emergency consultation completed'
  },
  {
    id: 'APT-004',
    patientName: 'Emily Wilson',
    patientId: 'P-004',
    doctorName: 'Dr. Emily Lee',
    department: 'Neurology',
    date: '2024-01-28',
    time: '02:00 PM',
    duration: '45 mins',
    type: 'Follow-up',
    status: 'Cancelled',
    priority: 'Normal',
    reason: 'Headache evaluation',
    phone: '+1-555-0129',
    notes: 'Patient cancelled due to scheduling conflict'
  },
  {
    id: 'APT-005',
    patientName: 'David Miller',
    patientId: 'P-005',
    doctorName: 'Dr. Robert Johnson',
    department: 'Orthopedics',
    date: '2024-01-28',
    time: '03:30 PM',
    duration: '30 mins',
    type: 'Consultation',
    status: 'No Show',
    priority: 'Low',
    reason: 'Knee pain assessment',
    phone: '+1-555-0131',
    notes: 'Patient did not show up for appointment'
  }
];

export const doctors = [
  'Dr. James Smith',
  'Dr. Sarah Williams',
  'Dr. Michael Davis',
  'Dr. Emily Lee',
  'Dr. Robert Johnson'
];

export const departments = [
  'Cardiology',
  'Pediatrics',
  'Emergency',
  'Neurology',
  'Orthopedics'
];

export const appointmentTypes = [
  'Consultation',
  'Check-up',
  'Follow-up',
  'Emergency',
  'Surgery'
];

export const priorityLevels = ['Low', 'Normal', 'High'];

export const appointmentStatuses = [
  'all',
  'scheduled',
  'in progress',
  'completed',
  'cancelled',
  'no show'
];

export const dateFilters = [
  { value: 'today', label: 'Today' },
  { value: 'tomorrow', label: 'Tomorrow' },
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' }
];
