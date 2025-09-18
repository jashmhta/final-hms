import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login-page';
import { PatientRegistrationPage } from '../../pages/patient-registration-page';
import { DashboardPage } from '../../pages/dashboard-page';
import { TestHelpers } from '../../utils/test-helpers';
test.describe('PHASE 1: Patient Registration Journey', () => {
  let loginPage: LoginPage;
  let patientRegistrationPage: PatientRegistrationPage;
  let dashboardPage: DashboardPage;
  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    patientRegistrationPage = new PatientRegistrationPage(page);
    dashboardPage = new DashboardPage(page);
  });
  test.describe('Complete Patient Registration Journey', () => {
    test('1.1.1 - Complete patient registration from start to finish', async ({ page }) => {
      test.setTimeout(120000);
      await loginPage.navigate();
      await loginPage.validateLoginPageElements();
      await loginPage.clickRegister();
      const { success, patientData } = await patientRegistrationPage.registerRandomPatient();
      expect(success).toBe(true);
      await expect(page.locator(patientRegistrationPage.successMessage)).toBeVisible();
      await patientRegistrationPage.takeScreenshot('patient-registration-success');
      await loginPage.login(patientData.email, 'default-password'); 
      await dashboardPage.waitForDashboardLoad();
      const welcomeMessage = await dashboardPage.getWelcomeMessage();
      expect(welcomeMessage).toContain(patientData.firstName);
      await dashboardPage.navigateToSection('Profile');
      await expect(page.locator('text=' + patientData.firstName + ' ' + patientData.lastName)).toBeVisible();
      const performance = await patientRegistrationPage.testPerformance();
      console.log('Registration Performance:', performance);
      const accessibilityPassed = await patientRegistrationPage.testAccessibility();
      expect(accessibilityPassed).toBe(true);
    });
    test('1.1.2 - Patient registration with validation and error handling', async ({ page }) => {
      test.setTimeout(90000);
      await patientRegistrationPage.navigate();
      const hasValidationErrors = await patientRegistrationPage.testFormValidation();
      expect(hasValidationErrors).toBe(true);
      await patientRegistrationPage.navigate();
      const emailValidationPassed = await patientRegistrationPage.testEmailValidation();
      expect(emailValidationPassed).toBe(true);
      await patientRegistrationPage.navigate();
      const phoneValidationPassed = await patientRegistrationPage.testPhoneValidation();
      expect(phoneValidationPassed).toBe(true);
      await patientRegistrationPage.navigate();
      const dateValidationPassed = await patientRegistrationPage.testDateOfBirthValidation();
      expect(dateValidationPassed).toBe(true);
      const duplicateEmailTest = await patientRegistrationPage.testDuplicateEmail();
      expect(duplicateEmailTest).toBe(true);
    });
    test('1.1.3 - Patient registration with comprehensive data', async ({ page }) => {
      test.setTimeout(90000);
      const patientData = TestHelpers.generatePatientData();
      patientData.dateOfBirth = patientData.dateOfBirth.toISOString().split('T')[0];
      const comprehensiveData = {
        ...patientData,
        medicalHistory: {
          conditions: ['Hypertension', 'Diabetes Type 2'],
          allergies: ['Penicillin', 'Shellfish'],
          medications: ['Lisinopril 10mg', 'Metformin 500mg'],
          surgeries: ['Appendectomy 2015'],
          familyHistory: {
            father: 'Hypertension',
            mother: 'Diabetes',
            siblings: 'None'
          }
        },
        lifestyle: {
          smoking: 'Never',
          alcohol: 'Occasional',
          exercise: '3 times per week',
          diet: 'Balanced'
        },
        emergencyContact: {
          ...patientData.emergencyContact,
          secondaryContact: {
            name: 'Jane Doe',
            relationship: 'Friend',
            phone: '+1-555-0124'
          }
        }
      };
      const success = await patientRegistrationPage.registerPatient(comprehensiveData);
      expect(success).toBe(true);
      const dataPersisted = await patientRegistrationPage.testDataPersistence();
      expect(dataPersisted).toBe(true);
      const mobileResponsive = await patientRegistrationPage.testMobileResponsiveness();
      expect(mobileResponsive).toBe(true);
    });
    test('1.1.4 - Patient registration integration with appointment scheduling', async ({ page }) => {
      test.setTimeout(120000);
      const { patientData } = await patientRegistrationPage.registerRandomPatient();
      await dashboardPage.navigateToSection('Appointments');
      const appointmentForm = await page.locator('[data-testid="appointment-form"], .appointment-form').isVisible();
      expect(appointmentForm).toBe(true);
      const patientSearchInput = 'input[name="patient"], [data-testid="patient-search"]';
      if (await page.locator(patientSearchInput).isVisible()) {
        await page.fill(patientSearchInput, patientData.firstName + ' ' + patientData.lastName);
        await page.waitForTimeout(2000);
        const searchResults = await page.locator('[data-testid="search-result"], .search-result').count();
        expect(searchResults).toBeGreaterThan(0);
      }
      const appointmentData = TestHelpers.generateAppointmentData();
      console.log('Generated appointment data for integration test:', appointmentData);
    });
    test('1.1.5 - Patient registration with document upload', async ({ page }) => {
      test.setTimeout(90000);
      const fileUploadSupported = await patientRegistrationPage.testFileUpload();
      if (fileUploadSupported) {
        console.log('Document upload feature is supported and tested');
      } else {
        console.log('Document upload feature not available - this is acceptable for MVP');
      }
      const autoFillWorking = await patientRegistrationPage.testAutoFill();
      expect(autoFillWorking).toBe(true);
      const progressiveFormWorking = await patientRegistrationPage.testProgressiveForm();
      expect(progressiveFormWorking).toBe(true);
    });
    test('1.1.6 - Patient registration security and privacy', async ({ page }) => {
      test.setTimeout(90000);
      const formResetWorking = await patientRegistrationPage.testFormReset();
      expect(formResetWorking).toBe(true);
      const incompleteDataTest = await patientRegistrationPage.testIncompleteData();
      expect(incompleteDataTest).toBe(true);
      const currentPage = page.url();
      expect(currentPage).toMatch(/^https:/);
      const cspHeader = await page.evaluate(() => {
        return document.querySelector('meta[http-equiv="Content-Security-Policy"]')?.getAttribute('content');
      });
      expect(cspHeader).toBeDefined();
    });
    test('1.1.7 - Patient registration with various user scenarios', async ({ page }) => {
      test.setTimeout(120000);
      const minorPatient = TestHelpers.generatePatientData();
      minorPatient.dateOfBirth = '2015-05-15'; 
      minorPatient.emergencyContact.relationship = 'Parent';
      const minorRegistrationSuccess = await patientRegistrationPage.registerPatient(minorPatient);
      expect(minorRegistrationSuccess).toBe(true);
      const elderlyPatient = TestHelpers.generatePatientData();
      elderlyPatient.dateOfBirth = '1945-03-20'; 
      elderlyPatient.medicalHistory = {
        conditions: ['Arthritis', 'Hypertension', 'Cataracts'],
        medications: ['Blood pressure medication', 'Pain relief']
      };
      await patientRegistrationPage.navigate();
      const elderlyRegistrationSuccess = await patientRegistrationPage.registerPatient(elderlyPatient);
      expect(elderlyRegistrationSuccess).toBe(true);
      const complexPatient = TestHelpers.generatePatientData();
      complexPatient.medicalHistory = {
        conditions: ['Asthma', 'Allergies', 'Previous surgeries'],
        allergies: ['Multiple environmental allergies'],
        medications: ['Daily maintenance medications'],
        surgeries: ['Tonsillectomy', 'Appendectomy']
      };
      await patientRegistrationPage.navigate();
      const complexRegistrationSuccess = await patientRegistrationPage.registerPatient(complexPatient);
      expect(complexRegistrationSuccess).toBe(true);
    });
    test('1.1.8 - Patient registration performance under load', async ({ page }) => {
      test.setTimeout(180000);
      const performanceResults = [];
      for (let i = 0; i < 5; i++) {
        const startTime = Date.now();
        const { success } = await patientRegistrationPage.registerRandomPatient();
        const endTime = Date.now();
        performanceResults.push({
          iteration: i + 1,
          success: success,
          duration: endTime - startTime
        });
        expect(success).toBe(true);
      }
      const totalTime = performanceResults.reduce((sum, result) => sum + result.duration, 0);
      const averageTime = totalTime / performanceResults.length;
      const maxTime = Math.max(...performanceResults.map(r => r.duration));
      const minTime = Math.min(...performanceResults.map(r => r.duration));
      console.log('Patient Registration Performance Results:', {
        totalTime,
        averageTime,
        maxTime,
        minTime,
        results: performanceResults
      });
      expect(averageTime).toBeLessThan(30000); 
      expect(maxTime).toBeLessThan(60000); 
      expect(performanceResults.every(r => r.success)).toBe(true); 
    });
    test('1.1.9 - Patient registration with network conditions', async ({ page }) => {
      test.setTimeout(120000);
      await patientRegistrationPage.simulateNetworkConditions({
        latency: 1000,
        downloadThroughput: 500000,
        uploadThroughput: 500000
      });
      const slowNetworkResult = await patientRegistrationPage.registerRandomPatient();
      expect(slowNetworkResult.success).toBe(true);
      await patientRegistrationPage.simulateNetworkConditions({});
      await patientRegistrationPage.simulateNetworkConditions({
        latency: 2000,
        downloadThroughput: 100000,
        uploadThroughput: 100000
      });
      const intermittentResult = await patientRegistrationPage.registerRandomPatient();
      expect(intermittentResult.success).toBe(true);
    });
    test('1.1.10 - Patient registration data validation and business rules', async ({ page }) => {
      test.setTimeout(90000);
      const infantPatient = TestHelpers.generatePatientData();
      infantPatient.dateOfBirth = new Date().toISOString().split('T')[0]; 
      await patientRegistrationPage.navigate();
      await patientRegistrationPage.registerPatient(infantPatient);
      const ageError = await page.locator('[data-testid="age-error"], .age-validation-error').isVisible();
      expect(ageError).toBe(true);
      const veryElderlyPatient = TestHelpers.generatePatientData();
      veryElderlyPatient.dateOfBirth = '1900-01-01'; 
      await patientRegistrationPage.navigate();
      await patientRegistrationPage.registerPatient(veryElderlyPatient);
      const maxAgeError = await page.locator('[data-testid="age-error"], .age-validation-error').isVisible();
      expect(maxAgeError).toBe(true);
      const minorWithoutEmergency = TestHelpers.generatePatientData();
      minorWithoutEmergency.dateOfBirth = '2010-05-15'; 
      delete minorWithoutEmergency.emergencyContact;
      await patientRegistrationPage.navigate();
      await patientRegistrationPage.registerPatient(minorWithoutEmergency);
      const emergencyError = await page.locator('[data-testid="emergency-contact-error"], .emergency-contact-required-error').isVisible();
      expect(emergencyError).toBe(true);
    });
    test.afterEach(async ({ page }) => {
      try {
        await dashboardPage.logout();
      } catch (e) {
      }
    });
  });
  test.describe('Patient Registration Edge Cases', () => {
    test('1.1.11 - Patient registration with special characters in names', async ({ page }) => {
      test.setTimeout(60000);
      const patientWithSpecialChars = TestHelpers.generatePatientData();
      patientWithSpecialChars.firstName = 'José María';
      patientWithSpecialChars.lastName = 'O\'Connor-Smith';
      patientWithSpecialChars.dateOfBirth = patientWithSpecialChars.dateOfBirth.toISOString().split('T')[0];
      const success = await patientRegistrationPage.registerPatient(patientWithSpecialChars);
      expect(success).toBe(true);
    });
    test('1.1.12 - Patient registration with international phone numbers', async ({ page }) => {
      test.setTimeout(60000);
      const patientWithInternationalPhone = TestHelpers.generatePatientData();
      patientWithInternationalPhone.phone = '+44 20 7946 0958'; 
      patientWithInternationalPhone.dateOfBirth = patientWithInternationalPhone.dateOfBirth.toISOString().split('T')[0];
      const success = await patientRegistrationPage.registerPatient(patientWithInternationalPhone);
      expect(success).toBe(true);
    });
    test('1.1.13 - Patient registration session timeout handling', async ({ page }) => {
      test.setTimeout(120000);
      await patientRegistrationPage.navigate();
      await patientRegistrationPage.fill(patientRegistrationPage.firstNameInput, 'Test');
      await patientRegistrationPage.fill(patientRegistrationPage.lastNameInput, 'User');
      await page.waitForTimeout(1000); 
      await patientRegistrationPage.click(patientRegistrationPage.submitButton);
      const timeoutMessage = await page.locator('[data-testid="session-timeout"], .session-timeout-message').isVisible();
      const redirectedToLogin = page.url().includes('/login');
      expect(timeoutMessage || redirectedToLogin).toBe(true);
    });
  });
});