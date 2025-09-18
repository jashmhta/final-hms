import { Page } from '@playwright/test';
import { BasePage } from './base-page';
import { TestHelpers } from '../utils/test-helpers';
export class PatientRegistrationPage extends BasePage {
  readonly registrationForm = '[data-testid="patient-registration-form"], .patient-registration-form';
  readonly firstNameInput = 'input[name="firstName"], [data-testid="first-name"]';
  readonly lastNameInput = 'input[name="lastName"], [data-testid="last-name"]';
  readonly dateOfBirthInput = 'input[name="dateOfBirth"], [data-testid="date-of-birth"]';
  readonly genderSelect = 'select[name="gender"], [data-testid="gender"]';
  readonly emailInput = 'input[name="email"], [data-testid="email"]';
  readonly phoneInput = 'input[name="phone"], [data-testid="phone"]';
  readonly addressStreetInput = 'input[name="address.street"], [data-testid="address-street"]';
  readonly addressCityInput = 'input[name="address.city"], [data-testid="address-city"]';
  readonly addressStateInput = 'input[name="address.state"], [data-testid="address-state"]';
  readonly addressZipInput = 'input[name="address.zipCode"], [data-testid="address-zip"]';
  readonly emergencyContactNameInput = 'input[name="emergencyContact.name"], [data-testid="emergency-name"]';
  readonly emergencyContactRelationshipInput = 'input[name="emergencyContact.relationship"], [data-testid="emergency-relationship"]';
  readonly emergencyContactPhoneInput = 'input[name="emergencyContact.phone"], [data-testid="emergency-phone"]';
  readonly insuranceProviderInput = 'input[name="insurance.provider"], [data-testid="insurance-provider"]';
  readonly insurancePolicyInput = 'input[name="insurance.policyNumber"], [data-testid="insurance-policy"]';
  readonly insuranceGroupInput = 'input[name="insurance.groupNumber"], [data-testid="insurance-group"]';
  readonly submitButton = 'button[type="submit"], [data-testid="submit-registration"], .submit-button';
  readonly cancelButton = 'button[type="button"], [data-testid="cancel-button"], .cancel-button';
  readonly successMessage = '[data-testid="success-message"], .success-message, .alert-success';
  readonly errorMessage = '[data-testid="error-message"], .error-message, .alert-danger';
  constructor(page: Page) {
    super(page, '/patient/register');
  }
  async registerPatient(patientData: any) {
    await this.navigate();
    await this.waitForVisible(this.registrationForm);
    await this.fill(this.firstNameInput, patientData.firstName);
    await this.fill(this.lastNameInput, patientData.lastName);
    await this.fill(this.dateOfBirthInput, patientData.dateOfBirth);
    await this.selectOption(this.genderSelect, patientData.gender);
    await this.fill(this.emailInput, patientData.email);
    await this.fill(this.phoneInput, patientData.phone);
    await this.fill(this.addressStreetInput, patientData.address.street);
    await this.fill(this.addressCityInput, patientData.address.city);
    await this.fill(this.addressStateInput, patientData.address.state);
    await this.fill(this.addressZipInput, patientData.address.zipCode);
    await this.fill(this.emergencyContactNameInput, patientData.emergencyContact.name);
    await this.fill(this.emergencyContactRelationshipInput, patientData.emergencyContact.relationship);
    await this.fill(this.emergencyContactPhoneInput, patientData.emergencyContact.phone);
    if (patientData.insurance) {
      await this.fill(this.insuranceProviderInput, patientData.insurance.provider);
      await this.fill(this.insurancePolicyInput, patientData.insurance.policyNumber);
      await this.fill(this.insuranceGroupInput, patientData.insurance.groupNumber);
    }
    await this.takeScreenshot('patient-registration-before-submit');
    await this.click(this.submitButton);
    await this.waitForPageLoad();
    return await this.waitForSuccess();
  }
  async registerRandomPatient() {
    const patientData = TestHelpers.generatePatientData();
    patientData.dateOfBirth = patientData.dateOfBirth.toISOString().split('T')[0];
    const success = await this.registerPatient(patientData);
    return { success, patientData };
  }
  async validateFormFields() {
    const requiredFields = [
      this.firstNameInput,
      this.lastNameInput,
      this.dateOfBirthInput,
      this.genderSelect,
      this.emailInput,
      this.phoneInput,
      this.emergencyContactNameInput,
      this.emergencyContactPhoneInput
    ];
    for (const field of requiredFields) {
      await this.waitForVisible(field);
    }
    return true;
  }
  async testFormValidation() {
    await this.navigate();
    await this.click(this.submitButton);
    const validationErrors = await this.page.locator('.error-message, [data-testid="error"], .invalid-feedback').count();
    return validationErrors > 0;
  }
  async testEmailValidation() {
    await this.navigate();
    await this.fill(this.emailInput, 'invalid-email');
    await this.click(this.submitButton);
    const emailError = await this.page.locator('input[name="email"] + .error-message, [data-testid="email-error"]').count();
    return emailError > 0;
  }
  async testPhoneValidation() {
    await this.navigate();
    await this.fill(this.phoneInput, '123');
    await this.click(this.submitButton);
    const phoneError = await this.page.locator('input[name="phone"] + .error-message, [data-testid="phone-error"]').count();
    return phoneError > 0;
  }
  async testDateOfBirthValidation() {
    await this.navigate();
    const futureDate = new Date();
    futureDate.setFullYear(futureDate.getFullYear() + 1);
    await this.fill(this.dateOfBirthInput, futureDate.toISOString().split('T')[0]);
    await this.click(this.submitButton);
    const dateError = await this.page.locator('input[name="dateOfBirth"] + .error-message, [data-testid="date-error"]').count();
    return dateError > 0;
  }
  async testDuplicateEmail() {
    const { patientData } = await this.registerRandomPatient();
    await this.navigate();
    const duplicateData = TestHelpers.generatePatientData();
    duplicateData.email = patientData.email;
    duplicateData.dateOfBirth = duplicateData.dateOfBirth.toISOString().split('T')[0];
    await this.registerPatient(duplicateData);
    const duplicateError = await this.isVisible(this.errorMessage);
    const errorMessage = await this.getText(this.errorMessage);
    return duplicateError && errorMessage.toLowerCase().includes('email');
  }
  async testIncompleteData() {
    await this.navigate();
    await this.fill(this.firstNameInput, 'John');
    await this.click(this.submitButton);
    const validationErrors = await this.page.locator('.error-message, [data-testid="error"], .invalid-feedback').count();
    return validationErrors > 0;
  }
  async testFileUpload() {
    await this.navigate();
    const fileInput = 'input[type="file"][name="documents"], [data-testid="document-upload"]';
    if (await this.isVisible(fileInput)) {
      const testFilePath = './test-data/test-document.pdf';
      await this.uploadFile(fileInput, testFilePath);
      const uploadedFile = await this.page.locator('[data-testid="uploaded-file"], .uploaded-file').count();
      return uploadedFile > 0;
    }
    return false;
  }
  async testAutoFill() {
    await this.navigate();
    await this.fill(this.addressZipInput, '90210'); 
    await this.page.waitForTimeout(1000);
    const cityValue = await this.page.getAttribute(this.addressCityInput, 'value');
    const stateValue = await this.page.getAttribute(this.addressStateInput, 'value');
    return cityValue === 'Beverly Hills' && stateValue === 'CA';
  }
  async testFormReset() {
    await this.navigate();
    await this.fill(this.firstNameInput, 'John');
    await this.fill(this.lastNameInput, 'Doe');
    await this.fill(this.emailInput, 'john@example.com');
    await this.click(this.cancelButton);
    const firstNameValue = await this.page.getAttribute(this.firstNameInput, 'value');
    const lastNameValue = await this.page.getAttribute(this.lastNameInput, 'value');
    const emailValue = await this.page.getAttribute(this.emailInput, 'value');
    return !firstNameValue && !lastNameValue && !emailValue;
  }
  async testProgressiveForm() {
    await this.navigate();
    const nextButton = '[data-testid="next-step"], .next-step-button';
    const prevButton = '[data-testid="previous-step"], .previous-step-button';
    if (await this.isVisible(nextButton)) {
      await this.fill(this.firstNameInput, 'John');
      await this.fill(this.lastNameInput, 'Doe');
      await this.click(nextButton);
      await this.waitForVisible(prevButton);
      await this.fill(this.emailInput, 'john@example.com');
      await this.fill(this.phoneInput, '555-0123');
      await this.click(prevButton);
      const firstNameValue = await this.page.getAttribute(this.firstNameInput, 'value');
      return firstNameValue === 'John';
    }
    return true; 
  }
  async testAccessibility() {
    await this.navigate();
    await this.waitForVisible(this.registrationForm);
    const accessibilityResults = await this.checkAccessibility();
    return accessibilityResults.violations.length === 0;
  }
  async testPerformance() {
    const startTime = Date.now();
    await this.navigate();
    await this.waitForVisible(this.registrationForm);
    const loadTime = Date.now() - startTime;
    const patientData = TestHelpers.generatePatientData();
    patientData.dateOfBirth = patientData.dateOfBirth.toISOString().split('T')[0];
    const submitStartTime = Date.now();
    await this.registerPatient(patientData);
    const submitTime = Date.now() - submitStartTime;
    return {
      pageLoadTime: loadTime,
      formSubmissionTime: submitTime,
      totalTime: loadTime + submitTime
    };
  }
  async testMobileResponsiveness() {
    await this.page.setViewportSize({ width: 375, height: 667 }); 
    await this.navigate();
    const formVisible = await this.isVisible(this.registrationForm);
    const inputsVisible = await this.isVisible(this.firstNameInput);
    await this.fill(this.firstNameInput, 'Test');
    const submitButtonVisible = await this.isVisible(this.submitButton);
    return formVisible && inputsVisible && submitButtonVisible;
  }
  async testDataPersistence() {
    const { patientData } = await this.registerRandomPatient();
    await this.page.waitForTimeout(2000);
    await this.page.goto('/patient/profile');
    const patientNameFound = await this.page.locator(`text=${patientData.firstName} ${patientData.lastName}`).count();
    return patientNameFound > 0;
  }
}