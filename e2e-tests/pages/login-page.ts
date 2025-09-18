import { Page } from '@playwright/test';
import { BasePage } from './base-page';
import { TestHelpers } from '../utils/test-helpers';
export class LoginPage extends BasePage {
  readonly usernameInput = 'input[name="username"], [data-testid="username"]';
  readonly passwordInput = 'input[name="password"], [data-testid="password"]';
  readonly loginButton = 'button[type="submit"], [data-testid="login-button"], .login-button';
  readonly errorMessage = '[data-testid="error-message"], .error-message, .alert-danger';
  readonly successMessage = '[data-testid="success-message"], .success-message, .alert-success';
  readonly forgotPasswordLink = '[data-testid="forgot-password"], .forgot-password';
  readonly registerLink = '[data-testid="register"], .register-link';
  readonly rememberMeCheckbox = 'input[name="remember"], [data-testid="remember-me"]';
  constructor(page: Page) {
    super(page, '/login');
  }
  async login(username: string, password: string, rememberMe = false) {
    await this.navigate();
    await this.fill(this.usernameInput, username);
    await this.fill(this.passwordInput, password);
    if (rememberMe) {
      await this.check(this.rememberMeCheckbox);
    }
    await this.click(this.loginButton);
    await this.waitForPageLoad();
    await this.takeScreenshot('login-attempt');
  }
  async loginAsAdmin() {
    const adminUsername = process.env.TEST_ADMIN_USERNAME || 'admin@hms.com';
    const adminPassword = process.env.TEST_ADMIN_PASSWORD || 'admin123';
    await this.login(adminUsername, adminPassword);
  }
  async loginAsDoctor() {
    const doctorUsername = process.env.TEST_DOCTOR_USERNAME || 'doctor@hms.com';
    const doctorPassword = process.env.TEST_DOCTOR_PASSWORD || 'doctor123';
    await this.login(doctorUsername, doctorPassword);
  }
  async loginAsPatient() {
    const patientUsername = process.env.TEST_PATIENT_USERNAME || 'patient@hms.com';
    const patientPassword = process.env.TEST_PATIENT_PASSWORD || 'patient123';
    await this.login(patientUsername, patientPassword);
  }
  async isLoginSuccessful() {
    return await this.isVisible(this.successMessage) ||
           await this.getCurrentURL().then(url => !url.includes('/login'));
  }
  async isLoginFailed() {
    return await this.isVisible(this.errorMessage);
  }
  async getErrorMessage() {
    return await this.getText(this.errorMessage);
  }
  async clickForgotPassword() {
    await this.click(this.forgotPasswordLink);
    await this.waitForPageLoad();
  }
  async clickRegister() {
    await this.click(this.registerLink);
    await this.waitForPageLoad();
  }
  async validateLoginPageElements() {
    await this.waitForVisible(this.usernameInput);
    await this.waitForVisible(this.passwordInput);
    await this.waitForVisible(this.loginButton);
    await this.waitForVisible(this.forgotPasswordLink);
    await this.waitForVisible(this.registerLink);
    await this.waitForVisible(this.rememberMeCheckbox);
  }
  async testInvalidLogin(username: string, password: string) {
    await this.login(username, password);
    await this.waitForVisible(this.errorMessage);
    const errorMessage = await this.getErrorMessage();
    return errorMessage;
  }
  async testEmptyCredentials() {
    await this.navigate();
    await this.click(this.loginButton);
    const validationErrors = await this.page.locator('.error-message, [data-testid="error"], .invalid-feedback').count();
    return validationErrors > 0;
  }
  async testPasswordVisibility() {
    await this.navigate();
    await this.fill(this.passwordInput, 'testpassword');
    const passwordType = await this.page.getAttribute(this.passwordInput, 'type');
    expect(passwordType).toBe('password');
    const toggleButton = 'button[type="button"][aria-label*="password"], [data-testid="toggle-password"]';
    if (await this.isVisible(toggleButton)) {
      await this.click(toggleButton);
      const newType = await this.page.getAttribute(this.passwordInput, 'type');
      expect(newType).toBe('text');
    }
  }
  async testRememberMe() {
    const username = TestHelpers.generateUniqueEmail('remember-test');
    const password = 'TestPassword123!';
    await this.login(username, password, true);
    await this.waitForSuccess();
    await this.page.context().clearCookies();
    await this.navigate();
    const filledUsername = await this.page.getAttribute(this.usernameInput, 'value');
    return filledUsername === username;
  }
  async testLoginWithEnterKey() {
    const username = TestHelpers.generateUniqueEmail('enter-test');
    const password = 'TestPassword123!';
    await this.navigate();
    await this.fill(this.usernameInput, username);
    await this.fill(this.passwordInput, password);
    await this.page.keyboard.press('Enter');
    await this.waitForPageLoad();
    return await this.isLoginSuccessful();
  }
  async testMultipleFailedAttempts() {
    const username = TestHelpers.generateUniqueEmail('failed-attempt');
    for (let i = 0; i < 3; i++) {
      await this.login(username, 'wrongpassword');
      await this.waitForVisible(this.errorMessage);
    }
    const errorMessage = await this.getErrorMessage();
    return errorMessage.toLowerCase().includes('locked') ||
           errorMessage.toLowerCase().includes('attempts') ||
           await this.isVisible('[data-testid="captcha"], .captcha-container');
  }
  async testSessionTimeout() {
    await this.loginAsAdmin();
    await this.waitForSuccess();
    await this.page.waitForTimeout(1000); 
    await this.page.goto('/dashboard');
    const currentUrl = await this.getCurrentURL();
    return currentUrl.includes('/login');
  }
  async testCSRFProtection() {
    await this.navigate();
    const csrfToken = await this.page.locator('input[name="csrfmiddlewaretoken"], [data-testid="csrf-token"]').count();
    return csrfToken > 0;
  }
  async testBruteForceProtection() {
    const username = TestHelpers.generateUniqueEmail('brute-force');
    for (let i = 0; i < 10; i++) {
      await this.login(username, `wrong${i}`);
      await this.waitForVisible(this.errorMessage);
    }
    const errorMessage = await this.getErrorMessage();
    return errorMessage.toLowerCase().includes('blocked') ||
           errorMessage.toLowerCase().includes('rate limit') ||
           errorMessage.toLowerCase().includes('too many attempts');
  }
}