const fs = require('fs');
const path = require('path');
const { faker } = require('@faker-js/faker');
console.log('📊 Generating test data for HMS Enterprise-Grade system...');
function generatePatientData() {
    return {
        id: faker.string.uuid(),
        firstName: faker.person.firstName(),
        lastName: faker.person.lastName(),
        dateOfBirth: faker.date.birthdate({ min: 1, max: 100 }).toISOString().split('T')[0],
        gender: faker.helpers.arrayElement(['Male', 'Female', 'Other']),
        email: faker.internet.email(),
        phone: faker.phone.number(),
        address: {
            street: faker.location.streetAddress(),
            city: faker.location.city(),
            state: faker.location.state(),
            zipCode: faker.location.zipCode(),
            country: 'USA'
        },
        emergencyContact: {
            name: faker.person.fullName(),
            relationship: faker.helpers.arrayElement(['Spouse', 'Parent', 'Sibling', 'Friend']),
            phone: faker.phone.number()
        },
        insurance: {
            provider: faker.helpers.arrayElement(['Blue Cross', 'Aetna', 'UnitedHealth', 'Cigna']),
            policyNumber: faker.string.alphanumeric(10),
            groupNumber: faker.string.alphanumeric(8)
        },
        medicalHistory: {
            conditions: faker.helpers.arrayElements([
                'Hypertension', 'Diabetes Type 2', 'Asthma', 'Arthritis', 'None'
            ], faker.number.int({ min: 0, max: 3 })),
            allergies: faker.helpers.arrayElements([
                'Penicillin', 'Shellfish', 'Peanuts', 'Latex', 'None'
            ], faker.number.int({ min: 0, max: 2 })),
            medications: faker.helpers.arrayElements([
                'Lisinopril 10mg', 'Metformin 500mg', 'Albuterol inhaler', 'Ibuprofen 400mg'
            ], faker.number.int({ min: 0, max: 3 })),
            surgeries: faker.helpers.arrayElements([
                'Appendectomy', 'Tonsillectomy', 'Knee surgery', 'C-section', 'None'
            ], faker.number.int({ min: 0, max: 2 }))
        }
    };
}
function generateAppointmentData(patientId) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return {
        id: faker.string.uuid(),
        patientId: patientId,
        date: tomorrow.toISOString().split('T')[0],
        time: faker.helpers.arrayElement(['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']),
        type: faker.helpers.arrayElement(['Consultation', 'Follow-up', 'Routine Checkup', 'Emergency']),
        reason: faker.lorem.sentence(),
        notes: faker.lorem.paragraph(),
        duration: faker.helpers.arrayElement([30, 45, 60]),
        status: faker.helpers.arrayElement(['Scheduled', 'Confirmed', 'Completed', 'Cancelled']),
        provider: {
            id: faker.string.uuid(),
            name: `Dr. ${faker.person.fullName()}`,
            specialty: faker.helpers.arrayElement(['Cardiology', 'Internal Medicine', 'Pediatrics', 'Emergency Medicine'])
        }
    };
}
function generatePrescriptionData(patientId) {
    return {
        id: faker.string.uuid(),
        patientId: patientId,
        medication: faker.helpers.arrayElement([
            'Amoxicillin', 'Ibuprofen', 'Lisinopril', 'Metformin', 'Atorvastatin',
            'Albuterol', 'Sertraline', 'Omeprazole', 'Losartan', 'Metoprolol'
        ]),
        dosage: faker.helpers.arrayElement(['500mg', '250mg', '10mg', '20mg', '40mg', '5mg']),
        frequency: faker.helpers.arrayElement([
            'Twice daily', 'Three times daily', 'Once daily', 'As needed', 'Every 4 hours'
        ]),
        duration: faker.helpers.arrayElement(['7 days', '10 days', '14 days', '30 days', '90 days']),
        instructions: faker.lorem.sentence(),
        refills: faker.number.int({ min: 0, max: 6 }),
        prescribedBy: `Dr. ${faker.person.fullName()}`,
        datePrescribed: new Date().toISOString().split('T')[0],
        status: faker.helpers.arrayElement(['Active', 'Completed', 'Cancelled'])
    };
}
function generateBillingData(patientId, appointmentId) {
    return {
        id: faker.string.uuid(),
        patientId: patientId,
        appointmentId: appointmentId,
        description: faker.helpers.arrayElement([
            'Office Visit', 'Consultation', 'Procedure', 'Laboratory Test', 'Imaging'
        ]),
        amount: faker.number.float({ min: 50, max: 500, precision: 0.01 }),
        insuranceBilled: faker.datatype.boolean(),
        insurancePaid: faker.datatype.boolean(),
        patientPaid: faker.datatype.boolean(),
        status: faker.helpers.arrayElement(['Pending', 'Processed', 'Paid', 'Overdue']),
        date: new Date().toISOString().split('T')[0],
        insuranceDetails: {
            provider: faker.helpers.arrayElement(['Blue Cross', 'Aetna', 'UnitedHealth', 'Cigna']),
            claimNumber: faker.string.alphanumeric(12),
            approvedAmount: faker.number.float({ min: 25, max: 450, precision: 0.01 })
        }
    };
}
function generateLabResultData(patientId, orderId) {
    const testTypes = [
        'Complete Blood Count', 'Comprehensive Metabolic Panel', 'Lipid Panel',
        'Thyroid Function Tests', 'HbA1c', 'Urinalysis', 'Cultures', 'X-ray', 'MRI', 'CT Scan'
    ];
    return {
        id: faker.string.uuid(),
        patientId: patientId,
        orderId: orderId,
        testType: faker.helpers.arrayElement(testTypes),
        result: faker.helpers.arrayElement(['Normal', 'Abnormal', 'Critical', 'Pending']),
        value: faker.number.float({ min: 0, max: 1000, precision: 0.1 }),
        unit: faker.helpers.arrayElement(['mg/dL', 'g/dL', 'U/L', 'mEq/L', 'pg/mL']),
        referenceRange: `${faker.number.float({ min: 0, max: 100, precision: 0.1 })} - ${faker.number.float({ min: 101, max: 200, precision: 0.1 })}`,
        performedBy: `Lab Tech ${faker.person.fullName()}`,
        datePerformed: new Date().toISOString().split('T')[0],
        dateResulted: new Date().toISOString().split('T')[0],
        notes: faker.lorem.sentence()
    };
}
function generateTestData() {
    console.log('🔄 Generating test data...');
    const patients = [];
    for (let i = 0; i < 20; i++) {
        patients.push(generatePatientData());
    }
    const appointments = [];
    patients.forEach(patient => {
        const numAppointments = faker.number.int({ min: 1, max: 5 });
        for (let i = 0; i < numAppointments; i++) {
            appointments.push(generateAppointmentData(patient.id));
        }
    });
    const prescriptions = [];
    patients.forEach(patient => {
        const numPrescriptions = faker.number.int({ min: 0, max: 3 });
        for (let i = 0; i < numPrescriptions; i++) {
            prescriptions.push(generatePrescriptionData(patient.id));
        }
    });
    const billing = [];
    appointments.forEach(appointment => {
        if (faker.datatype.boolean(0.7)) { 
            billing.push(generateBillingData(appointment.patientId, appointment.id));
        }
    });
    const labResults = [];
    const labOrders = appointments.filter(a => a.type === 'Consultation' || a.type === 'Follow-up');
    labOrders.forEach(order => {
        if (faker.datatype.boolean(0.6)) { 
            labResults.push(generateLabResultData(order.patientId, order.id));
        }
    });
    const testData = {
        patients,
        appointments,
        prescriptions,
        billing,
        labResults,
        metadata: {
            generatedAt: new Date().toISOString(),
            totalPatients: patients.length,
            totalAppointments: appointments.length,
            totalPrescriptions: prescriptions.length,
            totalBilling: billing.length,
            totalLabResults: labResults.length
        }
    };
    const dataFiles = [
        { name: 'patients', data: patients },
        { name: 'appointments', data: appointments },
        { name: 'prescriptions', data: prescriptions },
        { name: 'billing', data: billing },
        { name: 'lab-results', data: labResults }
    ];
    dataFiles.forEach(({ name, data }) => {
        const filePath = path.join('test-data', `${name}.json`);
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        console.log(`✅ Generated ${data.length} ${name} records`);
    });
    const completeDataPath = path.join('test-data', 'complete-test-data.json');
    fs.writeFileSync(completeDataPath, JSON.stringify(testData, null, 2));
    console.log(`✅ Generated complete test data with ${testData.metadata.totalPatients} patients`);
    console.log('🎉 Test data generation completed!');
    return testData;
}
if (require.main === module) {
    generateTestData();
}
module.exports = { generateTestData, generatePatientData, generateAppointmentData };