import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login-page';
import { ProviderDashboardPage } from '../../pages/provider-dashboard-page';
import { PatientManagementPage } from '../../pages/patient-management-page';
import { ClinicalDocumentationPage } from '../../pages/clinical-documentation-page';
import { OrderManagementPage } from '../../pages/order-management-page';
import { TelemedicinePage } from '../../pages/telemedicine-page';
import { TestHelpers } from '../../utils/test-helpers';

test.describe('PHASE 3: Healthcare Provider Journey', () => {
  let loginPage: LoginPage;
  let providerDashboardPage: ProviderDashboardPage;
  let patientManagementPage: PatientManagementPage;
  let clinicalDocumentationPage: ClinicalDocumentationPage;
  let orderManagementPage: OrderManagementPage;
  let telemedicinePage: TelemedicinePage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    providerDashboardPage = new ProviderDashboardPage(page);
    patientManagementPage = new PatientManagementPage(page);
    clinicalDocumentationPage = new ClinicalDocumentationPage(page);
    orderManagementPage = new OrderManagementPage(page);
    telemedicinePage = new TelemedicinePage(page);
  });

  test.describe('Provider Dashboard and Workflow', () => {
    test('3.1.1 - Complete provider dashboard functionality', async ({ page }) => {
      test.setTimeout(120000);

      // Login as healthcare provider
      await loginPage.navigate();
      await loginPage.login('dr.provider@hospital.com', 'ProviderPass123!');

      // Wait for provider dashboard
      await providerDashboardPage.waitForDashboardLoad();

      // Verify dashboard elements
      await expect(providerDashboardPage.todaySchedule).toBeVisible();
      await expect(providerDashboardPage.patientStats).toBeVisible();
      await expect(providerDashboardPage.criticalAlerts).toBeVisible();
      await expect(providerDashboardPage.quickActions).toBeVisible();

      // Test today's schedule management
      const scheduleWorking = await providerDashboardPage.testScheduleManagement();
      expect(scheduleWorking).toBe(true);

      // Test patient stats and metrics
      const statsWorking = await providerDashboardPage.testPatientStatistics();
      expect(statsWorking).toBe(true);

      // Test critical alerts handling
      const alertsWorking = await providerDashboardPage.testCriticalAlerts();
      expect(alertsWorking).toBe(true);

      // Test performance
      const performance = await providerDashboardPage.testPerformance();
      console.log('Provider Dashboard Performance:', performance);
      expect(performance.loadTime).toBeLessThan(3000);

      // Test accessibility
      const accessibilityPassed = await providerDashboardPage.testAccessibility();
      expect(accessibilityPassed).toBe(true);
    });

    test('3.1.2 - Provider schedule and time management', async ({ page }) => {
      test.setTimeout(90000);

      await loginPage.loginAsProvider();
      await providerDashboardPage.navigateToSection('Schedule');

      // Test daily schedule view
      await expect(page.locator('[data-testid="daily-schedule"]')).toBeVisible();

      // Test weekly schedule view
      await providerDashboardPage.switchToWeeklyView();
      await expect(page.locator('[data-testid="weekly-schedule"]')).toBeVisible();

      // Test monthly schedule view
      await providerDashboardPage.switchToMonthlyView();
      await expect(page.locator('[data-testid="monthly-schedule"]')).toBeVisible();

      // Test appointment availability management
      const availabilitySet = await providerDashboardPage.setAvailability({
        date: new Date().toISOString().split('T')[0],
        startTime: '09:00',
        endTime: '17:00',
        interval: 30
      });
      expect(availabilitySet).toBe(true);

      // Test time blocking
      const timeBlockWorking = await providerDashboardPage.testTimeBlocking();
      expect(timeBlockWorking).toBe(true);

      // Test schedule conflicts
      const conflictDetection = await providerDashboardPage.testConflictDetection();
      expect(conflictDetection).toBe(true);
    });

    test('3.1.3 - Provider notifications and communication', async ({ page }) => {
      test.setTimeout(90000);

      await loginPage.loginAsProvider();

      // Test notification center
      const notificationsWorking = await providerDashboardPage.testNotificationCenter();
      expect(notificationsWorking).toBe(true);

      // Test secure messaging
      const messagingWorking = await providerDashboardPage.testSecureMessaging();
      expect(messagingWorking).toBe(true);

      // Test urgent communication channels
      const urgentChannelsWorking = await providerDashboardPage.testUrgentCommunication();
      expect(urgentChannelsWorking).toBe(true);

      // Test communication preferences
      await providerDashboardPage.testCommunicationPreferences();
    });
  });

  test.describe('Patient Management Journey', () => {
    test('3.2.1 - Complete patient management workflow', async ({ page }) => {
      test.setTimeout(150000);

      await loginPage.loginAsProvider();
      await patientManagementPage.navigate();

      // Test patient search and filtering
      const searchWorking = await patientManagementPage.testPatientSearch();
      expect(searchWorking).toBe(true);

      // Test patient filtering
      const filteringWorking = await patientManagementPage.testPatientFiltering();
      expect(filteringWorking).toBe(true);

      // Test patient record access
      const patientId = await patientManagementPage.getPatientId('John Doe');
      if (patientId) {
        await patientManagementPage.accessPatientRecord(patientId);
        await expect(page.locator('[data-testid="patient-record"]')).toBeVisible();

        // Test patient demographics
        await expect(page.locator('[data-testid="patient-demographics"]')).toBeVisible();

        // Test medical history
        await expect(page.locator('[data-testid="medical-history"]')).toBeVisible();

        // Test medications
        await expect(page.locator('[data-testid="current-medications"]')).toBeVisible();

        // Test allergies
        await expect(page.locator('[data-testid="allergies-list"]')).toBeVisible();
      }

      // Test patient list management
      const listManagementWorking = await patientManagementPage.testListManagement();
      expect(listManagementWorking).toBe(true);
    });

    test('3.2.2 - Patient encounter management', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsProvider();
      await patientManagementPage.navigate();

      // Start new patient encounter
      const encounterStarted = await patientManagementPage.startNewEncounter('John Doe');
      expect(encounterStarted).toBe(true);

      // Test encounter documentation
      const documentationWorking = await patientManagementPage.testEncounterDocumentation();
      expect(documentationWorking).toBe(true);

      // Test encounter workflow management
      const workflowWorking = await patientManagementPage.testEncounterWorkflow();
      expect(workflowWorking).toBe(true);

      // Test encounter completion
      const completionWorking = await patientManagementPage.testEncounterCompletion();
      expect(completionWorking).toBe(true);
    });

    test('3.2.3 - Patient follow-up and care coordination', async ({ page }) => {
      test.setTimeout(90000);

      await loginPage.loginAsProvider();
      await patientManagementPage.navigate();

      // Test follow-up scheduling
      const followUpWorking = await patientManagementPage.testFollowUpScheduling();
      expect(followUpWorking).toBe(true);

      // Test care coordination
      const coordinationWorking = await patientManagementPage.testCareCoordination();
      expect(coordinationWorking).toBe(true);

      // Test referral management
      const referralWorking = await patientManagementPage.testReferralManagement();
      expect(referralWorking).toBe(true);

      // Test care team communication
      const teamCommunicationWorking = await patientManagementPage.testTeamCommunication();
      expect(teamCommunicationWorking).toBe(true);
    });
  });

  test.describe('Clinical Documentation Journey', () => {
    test('3.3.1 - Complete clinical documentation workflow', async ({ page }) => {
      test.setTimeout(150000);

      await loginPage.loginAsProvider();
      await clinicalDocumentationPage.navigate();

      // Test SOAP note creation
      const soapNoteCreated = await clinicalDocumentationPage.createSOAPNote({
        subjective: 'Patient reports headache for 3 days',
        objective: 'Vitals: BP 120/80, HR 72, Temp 98.6°F',
        assessment: 'Tension headache',
        plan: 'Recommend OTC pain relievers and follow up in 1 week'
      });
      expect(soapNoteCreated).toBe(true);

      // Test progress notes
      const progressNoteWorking = await clinicalDocumentationPage.testProgressNotes();
      expect(progressNoteWorking).toBe(true);

      // Test templates and shortcuts
      const templatesWorking = await clinicalDocumentationPage.testTemplates();
      expect(templatesWorking).toBe(true);

      // Test voice-to-text
      const voiceToTextWorking = await clinicalDocumentationPage.testVoiceToText();
      expect(voiceToTextWorking).toBe(true);

      // Test document review and sign-off
      const reviewWorking = await clinicalDocumentationPage.testDocumentReview();
      expect(reviewWorking).toBe(true);
    });

    test('3.3.2 - Medical coding and billing integration', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsProvider();
      await clinicalDocumentationPage.navigate();

      // Test medical coding assistance
      const codingWorking = await clinicalDocumentationPage.testMedicalCoding();
      expect(codingWorking).toBe(true);

      // Test billing code assignment
      const billingCodeWorking = await clinicalDocumentationPage.testBillingCodeAssignment();
      expect(billingCodeWorking).toBe(true);

      // Test coding compliance
      const complianceWorking = await clinicalDocumentationPage.testCodingCompliance();
      expect(complianceWorking).toBe(true);

      // Test charge capture
      const chargeCaptureWorking = await clinicalDocumentationPage.testChargeCapture();
      expect(chargeCaptureWorking).toBe(true);
    });

    test('3.3.3 - Clinical decision support integration', async ({ page }) => {
      test.setTimeout(90000);

      await loginPage.loginAsProvider();
      await clinicalDocumentationPage.navigate();

      // Test clinical alerts
      const alertsWorking = await clinicalDocumentationPage.testClinicalAlerts();
      expect(alertsWorking).toBe(true);

      // Test drug interaction checking
      const interactionWorking = await clinicalDocumentationPage.testDrugInteractions();
      expect(interactionWorking).toBe(true);

      // Test clinical guidelines
      const guidelinesWorking = await clinicalDocumentationPage.testClinicalGuidelines();
      expect(guidelinesWorking).toBe(true);

      // Test diagnostic support
      const diagnosticWorking = await clinicalDocumentationPage.testDiagnosticSupport();
      expect(diagnosticWorking).toBe(true);
    });
  });

  test.describe('Order Management Journey', () => {
    test('3.4.1 - Complete laboratory orders workflow', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsProvider();
      await orderManagementPage.navigate();

      // Test lab order creation
      const labOrderCreated = await orderManagementPage.createLabOrder({
        patientId: 'PATIENT123',
        tests: ['CBC', 'CMP', 'Lipid Panel'],
        priority: 'Routine',
        clinicalIndication: 'Annual physical'
      });
      expect(labOrderCreated).toBe(true);

      // Test order tracking
      const trackingWorking = await orderManagementPage.testOrderTracking();
      expect(trackingWorking).toBe(true);

      // Test results review
      const resultsWorking = await orderManagementPage.testResultsReview();
      expect(resultsWorking).toBe(true);

      // Test critical value notification
      const criticalValueWorking = await orderManagementPage.testCriticalValueNotification();
      expect(criticalValueWorking).toBe(true);

      // Test order modification/cancellation
      const modificationWorking = await orderManagementPage.testOrderModification();
      expect(modificationWorking).toBe(true);
    });

    test('3.4.2 - Radiology and imaging orders', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsProvider();
      await orderManagementPage.navigateToSection('Radiology');

      // Test imaging order creation
      const imagingOrderCreated = await orderManagementPage.createImagingOrder({
        patientId: 'PATIENT123',
        procedure: 'Chest X-ray',
        contrast: 'None',
        priority: 'Routine',
        clinicalIndication: 'Chest pain evaluation'
      });
      expect(imagingOrderCreated).toBe(true);

      // Test scheduling coordination
      const schedulingWorking = await orderManagementPage.testImagingScheduling();
      expect(schedulingWorking).toBe(true);

      // Test image viewing
      const viewingWorking = await orderManagementPage.testImageViewing();
      expect(viewingWorking).toBe(true);

      // Test radiology report review
      const reportWorking = await orderManagementPage.testReportReview();
      expect(reportWorking).toBe(true);
    });

    test('3.4.3 - Medication and pharmacy orders', async ({ page }) => {
      test.setTimeout(120000);

      await loginPage.loginAsProvider();
      await orderManagementPage.navigateToSection('Pharmacy');

      // Test prescription ordering
      const prescriptionCreated = await orderManagementPage.createPrescription({
        patientId: 'PATIENT123',
        medication: 'Lisinopril 10mg',
        dosage: '1 tablet daily',
        quantity: 30,
        refills: 3,
        indications: 'Hypertension'
      });
      expect(prescriptionCreated).toBe(true);

      // Test pharmacy communication
      const pharmacyWorking = await orderManagementPage.testPharmacyCommunication();
      expect(pharmacyWorking).toBe(true);

      // Test medication reconciliation
      const reconciliationWorking = await orderManagementPage.testMedicationReconciliation();
      expect(reconciliationWorking).toBe(true);

      // Test formulary checking
      const formularyWorking = await orderManagementPage.testFormularyChecking();
      expect(formularyWorking).toBe(true);
    });
  });

  test.describe('Telemedicine Journey', () => {
    test('3.5.1 - Complete telemedicine workflow', async ({ page }) => {
      test.setTimeout(150000);

      await loginPage.loginAsProvider();
      await telemedicinePage.navigate();

      // Test virtual appointment scheduling
      const virtualAppointment = await telemedicinePage.scheduleVirtualAppointment({
        patientId: 'PATIENT123',
        date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
        time: '14:00',
        duration: 30,
        platform: 'Zoom'
      });
      expect(virtualAppointment).toBe(true);

      // Test pre-visit preparation
      const preparationWorking = await telemedicinePage.testPreVisitPreparation();
      expect(preparationWorking).toBe(true);

      // Test virtual visit execution
      const visitWorking = await telemedicinePage.testVirtualVisit();
      expect(visitWorking).toBe(true);

      // Test post-visit documentation
      const documentationWorking = await telemedicinePage.testPostVisitDocumentation();
      expect(documentationWorking).toBe(true);

      // Test technical support
      const supportWorking = await telemedicinePage.testTechnicalSupport();
      expect(supportWorking).toBe(true);
    });

    test('3.5.2 - Remote patient monitoring integration', async ({ page }) => {
      test.setTimeout(90000);

      await loginPage.loginAsProvider();
      await telemedicinePage.navigateToSection('Remote Monitoring');

      // Test device data integration
      const deviceIntegrationWorking = await telemedicinePage.testDeviceIntegration();
      expect(deviceIntegrationWorking).toBe(true);

      // Test vital signs monitoring
      const monitoringWorking = await telemedicinePage.testVitalSignsMonitoring();
      expect(monitoringWorking).toBe(true);

      // Test alert management
      const alertManagementWorking = await telemedicinePage.testRemoteAlertManagement();
      expect(alertManagementWorking).toBe(true);

      // Test patient compliance tracking
      const complianceWorking = await telemedicinePage.testComplianceTracking();
      expect(complianceWorking).toBe(true);
    });
  });

  test.describe('Provider Mobile Journey', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('3.6.1 - Complete provider workflow on mobile', async ({ page }) => {
      test.setTimeout(120000);

      // Mobile login
      await loginPage.navigate();
      await loginPage.testMobileLogin();

      // Test mobile dashboard
      await providerDashboardPage.waitForDashboardLoad();
      await providerDashboardPage.testMobileDashboard();

      // Test mobile patient management
      await patientManagementPage.navigate();
      await patientManagementPage.testMobilePatientManagement();

      // Test mobile clinical documentation
      await clinicalDocumentationPage.navigate();
      await clinicalDocumentationPage.testMobileDocumentation();

      // Test mobile order management
      await orderManagementPage.navigate();
      await orderManagementPage.testMobileOrders();
    });
  });

  test.afterEach(async ({ page }) => {
    try {
      await providerDashboardPage.logout();
    } catch (e) {
      console.log('Logout failed:', e);
    }
  });
});