import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login-page';
import { PatientDashboardPage } from '../../pages/patient-dashboard-page';
import { AppointmentsPage } from '../../pages/appointments-page';
import { MedicalRecordsPage } from '../../pages/medical-records-page';
import { BillingPage } from '../../pages/billing-page';
import { TestHelpers } from '../../utils/test-helpers';

test.describe('PHASE 2: Complete Patient Journey', () => {
  let loginPage: LoginPage;
  let patientDashboardPage: PatientDashboardPage;
  let appointmentsPage: AppointmentsPage;
  let medicalRecordsPage: MedicalRecordsPage;
  let billingPage: BillingPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    patientDashboardPage = new PatientDashboardPage(page);
    appointmentsPage = new AppointmentsPage(page);
    medicalRecordsPage = new MedicalRecordsPage(page);
    billingPage = new BillingPage(page);
  });

  test.describe('Patient Dashboard Journey', () => {
    test('2.1.1 - Complete patient dashboard navigation and features', async ({ page }) => {
      test.setTimeout(120000);

      // Login as existing patient
      await loginPage.navigate();
      await loginPage.login('existing.patient@example.com', 'SecurePass123!');

      // Wait for dashboard load
      await patientDashboardPage.waitForDashboardLoad();

      // Verify dashboard elements
      await expect(patientDashboardPage.welcomeMessage).toBeVisible();
      await expect(patientDashboardPage.quickActionsSection).toBeVisible();
      await expect(patientDashboardPage.upcomingAppointments).toBeVisible();
      await expect(patientDashboardPage.recentMedicalRecords).toBeVisible();

      // Test navigation to different sections
      await patientDashboardPage.navigateToSection('Profile');
      await expect(page.locator('[data-testid="profile-section"]')).toBeVisible();

      await patientDashboardPage.navigateToSection('Medical History');
      await expect(page.locator('[data-testid="medical-history-section"]')).toBeVisible();

      await patientDashboardPage.navigateToSection('Documents');
      await expect(page.locator('[data-testid="documents-section"]')).toBeVisible();

      // Test quick actions
      await patientDashboardPage.testQuickActions();

      // Test accessibility
      const accessibilityPassed = await patientDashboardPage.testAccessibility();
      expect(accessibilityPassed).toBe(true);

      // Test performance
      const performance = await patientDashboardPage.testPerformance();
      console.log('Dashboard Performance:', performance);
      expect(performance.loadTime).toBeLessThan(5000);
    });

    test('2.1.2 - Patient profile management journey', async ({ page }) => {
      test.setTimeout(90000);

      await loginPage.loginAsPatient();
      await patientDashboardPage.navigateToSection('Profile');

      // Test profile viewing
      await expect(page.locator('[data-testid="profile-display"]')).toBeVisible();

      // Test profile editing
      await patientDashboardPage.clickEditProfile();
      await expect(page.locator('[data-testid="profile-edit-form"]')).toBeVisible();

      // Update profile information
      const updatedData = {
        phone: '+1-555-NEW-NUMBER',
        address: '123 Updated Street, City, State 12345',
        emergencyContact: {
          name: 'Updated Emergency Contact',
          phone: '+1-555-EMERGENCY'
        }
      };

      await patientDashboardPage.updateProfile(updatedData);

      // Verify changes are saved
      await expect(page.locator('[data-testid="success-message"]')).toBeVisible();

      // Test profile photo upload
      const photoUploadWorking = await patientDashboardPage.testProfilePhotoUpload();
      expect(photoUploadWorking).toBe(true);

      // Test privacy settings
      await patientDashboardPage.testPrivacySettings();
    });

    test('2.1.3 - Patient medical history journey', async ({ page }) => {
      test.setTimeout(90000);

      await loginPage.loginAsPatient();
      await patientDashboardPage.navigateToSection('Medical History');

      // Verify medical history display
      await expect(page.locator('[data-testid="medical-conditions"]')).toBeVisible();
      await expect(page.locator('[data-testid="allergies"]')).toBeVisible();
      await expect(page.locator('[data-testid="medications"]')).toBeVisible();

      // Test adding new medical information
      await patientDashboardPage.addMedicalCondition('New Test Condition', 'Test diagnosis notes');
      await expect(page.locator('[data-testid="condition-added-success"]')).toBeVisible();

      // Test allergies management
      await patientDashboardPage.addAllergy('Test Allergy', 'Mild reaction');
      await expect(page.locator('[data-testid="allergy-added-success"]')).toBeVisible();

      // Test medications tracking
      await patientDashboardPage.addMedication('Test Medication', '10mg', 'Daily');
      await expect(page.locator('[data-testid="medication-added-success"]')).toBeVisible();

      // Test medical history export
      const exportWorking = await patientDashboardPage.testMedicalHistoryExport();
      expect(exportWorking).toBe(true);
    });
  });

  test.describe('Appointment Management Journey', () => {
    test('2.2.1 - Complete appointment scheduling workflow', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsPatient();
      await appointmentsPage.navigate();

      // Test appointment scheduling
      const appointmentData = TestHelpers.generateAppointmentData();
      const appointmentScheduled = await appointmentsPage.scheduleAppointment(appointmentData);
      expect(appointmentScheduled).toBe(true);

      // Verify appointment appears in upcoming appointments
      await appointmentsPage.refreshAppointments();
      const upcomingAppointments = await appointmentsPage.getUpcomingAppointments();
      expect(upcomingAppointments.length).toBeGreaterThan(0);

      // Test appointment details view
      await appointmentsPage.viewAppointmentDetails(upcomingAppointments[0].id);
      await expect(page.locator('[data-testid="appointment-details"]')).toBeVisible();

      // Test appointment modification
      const modificationSuccess = await appointmentsPage.modifyAppointment(upcomingAppointments[0].id);
      expect(modificationSuccess).toBe(true);

      // Test appointment cancellation
      const cancellationSuccess = await appointmentsPage.cancelAppointment(upcomingAppointments[0].id);
      expect(cancellationSuccess).toBe(true);
    });

    test('2.2.2 - Appointment scheduling with different providers', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsPatient();
      await appointmentsPage.navigate();

      // Test scheduling with different provider types
      const providerTypes = ['General Practitioner', 'Specialist', 'Surgeon'];

      for (const providerType of providerTypes) {
        const appointmentData = {
          ...TestHelpers.generateAppointmentData(),
          providerType: providerType
        };

        const success = await appointmentsPage.scheduleAppointment(appointmentData);
        expect(success).toBe(true);

        // Verify provider-specific requirements
        if (providerType === 'Specialist') {
          const referralRequired = await appointmentsPage.verifyReferralRequirement();
          expect(referralRequired).toBe(true);
        }

        // Cancel appointment for next iteration
        const upcomingAppointments = await appointmentsPage.getUpcomingAppointments();
        if (upcomingAppointments.length > 0) {
          await appointmentsPage.cancelAppointment(upcomingAppointments[0].id);
        }
      }
    });

    test('2.2.3 - Appointment availability and time slot management', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsPatient();
      await appointmentsPage.navigate();

      // Test available time slots
      const availableSlots = await appointmentsPage.getAvailableTimeSlots();
      expect(availableSlots.length).toBeGreaterThan(0);

      // Test booking during different time periods
      const timeSlots = ['morning', 'afternoon', 'evening'];

      for (const timeSlot of timeSlots) {
        const slotAvailable = await appointmentsPage.checkTimeSlotAvailability(timeSlot);
        if (slotAvailable) {
          const appointmentData = {
            ...TestHelpers.generateAppointmentData(),
            preferredTime: timeSlot
          };

          const success = await appointmentsPage.scheduleAppointment(appointmentData);
          expect(success).toBe(true);

          // Cancel for next test
          const upcomingAppointments = await appointmentsPage.getUpcomingAppointments();
          if (upcomingAppointments.length > 0) {
            await appointmentsPage.cancelAppointment(upcomingAppointments[0].id);
          }
        }
      }
    });
  });

  test.describe('Medical Records Journey', () => {
    test('2.3.1 - Complete medical records access and management', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsPatient();
      await medicalRecordsPage.navigate();

      // Test medical records listing
      await expect(medicalRecordsPage.recordsTable).toBeVisible();

      // Test record filtering and search
      await medicalRecordsPage.searchRecords('Test Record');
      const searchResults = await medicalRecordsPage.getSearchResults();
      expect(searchResults.length).toBeGreaterThan(0);

      // Test record viewing
      const firstRecord = await medicalRecordsPage.getFirstRecord();
      await medicalRecordsPage.viewRecord(firstRecord.id);
      await expect(page.locator('[data-testid="record-details"]')).toBeVisible();

      // Test record download
      const downloadSuccess = await medicalRecordsPage.downloadRecord(firstRecord.id);
      expect(downloadSuccess).toBe(true);

      // Test record sharing with providers
      const shareSuccess = await medicalRecordsPage.shareRecordWithProvider(firstRecord.id, 'test.provider@hospital.com');
      expect(shareSuccess).toBe(true);

      // Test record access history
      await medicalRecordsPage.viewAccessHistory(firstRecord.id);
      await expect(page.locator('[data-testid="access-history"]')).toBeVisible();
    });

    test('2.3.2 - Medical records privacy and security', async ({ page }) => {
      test.setTimeout(90000);

      await loginPage.loginAsPatient();
      await medicalRecordsPage.navigate();

      // Test access controls
      const accessControlsWorking = await medicalRecordsPage.testAccessControls();
      expect(accessControlsWorking).toBe(true);

      // Test data encryption indicators
      const encryptionIndicators = await medicalRecordsPage.verifyEncryptionIndicators();
      expect(encryptionIndicators).toBe(true);

      // Test audit trail viewing
      await medicalRecordsPage.viewAuditTrail();
      await expect(page.locator('[data-testid="audit-trail"]')).toBeVisible();

      // Test consent management
      await medicalRecordsPage.manageConsentSettings();
      await expect(page.locator('[data-testid="consent-settings"]')).toBeVisible();
    });

    test('2.3.3 - Medical records integration with other systems', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsPatient();
      await medicalRecordsPage.navigate();

      // Test lab results integration
      const labResultsIntegrated = await medicalRecordsPage.testLabResultsIntegration();
      expect(labResultsIntegrated).toBe(true);

      // Test pharmacy integration
      const pharmacyIntegrated = await medicalRecordsPage.testPharmacyIntegration();
      expect(pharmacyIntegrated).toBe(true);

      // Test insurance integration
      const insuranceIntegrated = await medicalRecordsPage.testInsuranceIntegration();
      expect(insuranceIntegrated).toBe(true);
    });
  });

  test.describe('Billing and Insurance Journey', () => {
    test('2.4.1 - Complete billing and payment workflow', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsPatient();
      await billingPage.navigate();

      // Test billing dashboard
      await expect(billingPage.billingSummary).toBeVisible();
      await expect(billingPage.recentInvoices).toBeVisible();
      await expect(billingPage.paymentMethods).toBeVisible();

      // Test invoice viewing
      const invoices = await billingPage.getInvoices();
      expect(invoices.length).toBeGreaterThan(0);

      await billingPage.viewInvoice(invoices[0].id);
      await expect(page.locator('[data-testid="invoice-details"]')).toBeVisible();

      // Test payment processing
      const paymentSuccess = await billingPage.processPayment(invoices[0].id, 'credit_card');
      expect(paymentSuccess).toBe(true);

      // Test payment history
      await billingPage.viewPaymentHistory();
      await expect(page.locator('[data-testid="payment-history"]')).toBeVisible();

      // Test billing statements
      const statementDownload = await billingPage.downloadStatement();
      expect(statementDownload).toBe(true);
    });

    test('2.4.2 - Insurance claims and coverage verification', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsPatient();
      await billingPage.navigate();

      // Test insurance information display
      await expect(billingPage.insuranceInfo).toBeVisible();

      // Test coverage verification
      const coverageVerified = await billingPage.verifyCoverage('PROCEDURE_CODE_123');
      expect(coverageVerified).toBe(true);

      // Test claims submission
      const claimSubmitted = await billingPage.submitClaim({
        procedureCode: 'PROCEDURE_CODE_123',
        dateOfService: new Date().toISOString().split('T')[0],
        amount: 500.00
      });
      expect(claimSubmitted).toBe(true);

      // Test claims tracking
      await billingPage.trackClaims();
      await expect(page.locator('[data-testid="claims-tracking"]')).toBeVisible();

      // Test explanation of benefits
      const eobAvailable = await billingPage.viewExplanationOfBenefits();
      expect(eobAvailable).toBe(true);
    });

    test('2.4.3 - Billing dispute and resolution journey', async ({ page }) => {
      test.setTimeout(90000);

      await loginPage.loginAsPatient();
      await billingPage.navigate();

      // Test dispute initiation
      const disputeInitiated = await billingPage.initiateDispute({
        invoiceId: 'INV123',
        reason: 'Incorrect charges',
        amount: 100.00,
        description: 'This charge was for services not rendered'
      });
      expect(disputeInitiated).toBe(true);

      // Test dispute tracking
      await billingPage.trackDisputes();
      await expect(page.locator('[data-testid="dispute-tracking"]')).toBeVisible();

      // Test dispute resolution communication
      const communicationWorking = await billingPage.testDisputeCommunication();
      expect(communicationWorking).toBe(true);
    });
  });

  test.describe('Mobile Responsiveness Journey', () => {
    test.beforeEach(async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('2.5.1 - Complete patient journey on mobile device', async ({ page }) => {
      test.setTimeout(120000);

      // Login on mobile
      await loginPage.navigate();
      await loginPage.testMobileLogin();

      // Test mobile dashboard
      await patientDashboardPage.waitForDashboardLoad();
      await patientDashboardPage.testMobileNavigation();

      // Test mobile appointment scheduling
      await appointmentsPage.navigate();
      await appointmentsPage.testMobileScheduling();

      // Test mobile medical records access
      await medicalRecordsPage.navigate();
      await medicalRecordsPage.testMobileRecordAccess();

      // Test mobile billing
      await billingPage.navigate();
      await billingPage.testMobileBilling();
    });
  });

  test.afterEach(async ({ page }) => {
    try {
      await patientDashboardPage.logout();
    } catch (e) {
      console.log('Logout failed:', e);
    }
  });
});