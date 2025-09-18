import { Page, expect } from '@playwright/test';
import { faker } from '@faker-js/faker';
import { v4 as uuidv4 } from 'uuid';
export class TestHelpers {
  static generatePatientData() {
    return {
      firstName: faker.person.firstName(),
      lastName: faker.person.lastName(),
      dateOfBirth: faker.date.birthdate({ min: 1, max: 100 }),
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
      medicalRecordNumber: `MRN-${faker.number.int({ min: 100000, max: 999999 })}`,
      insurance: {
        provider: faker.helpers.arrayElement(['Blue Cross', 'Aetna', 'UnitedHealth', 'Cigna']),
        policyNumber: faker.string.alphanumeric(10),
        groupNumber: faker.string.alphanumeric(8)
      }
    };
  }
  static generateAppointmentData() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return {
      date: tomorrow.toISOString().split('T')[0],
      time: faker.helpers.arrayElement(['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']),
      type: faker.helpers.arrayElement(['Consultation', 'Follow-up', 'Routine Checkup', 'Emergency']),
      reason: faker.lorem.sentence(),
      notes: faker.lorem.paragraph(),
      duration: faker.helpers.arrayElement([30, 45, 60])
    };
  }
  static generatePrescriptionData() {
    return {
      medication: faker.helpers.arrayElement(['Amoxicillin', 'Ibuprofen', 'Lisinopril', 'Metformin', 'Atorvastatin']),
      dosage: faker.helpers.arrayElement(['500mg', '250mg', '10mg', '20mg', '40mg']),
      frequency: faker.helpers.arrayElement(['Twice daily', 'Three times daily', 'Once daily', 'As needed']),
      duration: faker.helpers.arrayElement(['7 days', '10 days', '14 days', '30 days']),
      instructions: faker.lorem.sentence(),
      refills: faker.number.int({ min: 0, max: 6 })
    };
  }
  static async waitForAPIResponse(page: Page, urlPattern: string, timeout = 30000) {
    const response = await page.waitForResponse(response =>
      response.url().includes(urlPattern) && response.status() === 200,
      { timeout }
    );
    return await response.json();
  }
  static async waitForSuccess(page: Page, timeout = 10000) {
    await expect(page.locator('[data-testid="success-message"], .success, .alert-success')).toBeVisible({ timeout });
  }
  static async waitForLoadingComplete(page: Page) {
    await page.waitForSelector('[data-testid="loading"], .loading, .spinner', { state: 'detached' });
    await page.waitForLoadState('networkidle');
  }
  static async takeScreenshot(page: Page, name: string) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await page.screenshot({
      path: `./screenshots/${name}-${timestamp}.png`,
      fullPage: true
    });
  }
  static getTimestamp() {
    return new Date().toISOString().replace(/[:.]/g, '-');
  }
  static generateUniqueEmail(prefix = 'test') {
    return `${prefix}-${uuidv4()}@test.com`;
  }
  static async fillForm(page: Page, data: Record<string, any>, prefix = '') {
    for (const [key, value] of Object.entries(data)) {
      const selector = prefix ? `${prefix}[name="${key}"]` : `[name="${key}"]`;
      if (typeof value === 'object' && value !== null) {
        await this.fillForm(page, value, `${prefix}${key}.`);
      } else {
        await page.fill(selector, String(value));
      }
    }
  }
  static async checkValidationErrors(page: Page, expectedErrors: string[]) {
    const errorElements = page.locator('.error-message, [data-testid="error"], .invalid-feedback');
    const errorCount = await errorElements.count();
    expect(errorCount).toBe(expectedErrors.length);
    for (let i = 0; i < errorCount; i++) {
      const errorText = await errorElements.nth(i).textContent();
      expect(expectedErrors).toContain(errorText?.trim());
    }
  }
  static async checkAccessibility(page: Page) {
    const AxeBuilder = require('@axe-core/playwright').default;
    const axeBuilder = new AxeBuilder({ page });
    const results = await axeBuilder.analyze();
    if (results.violations.length > 0) {
      console.log('Accessibility violations found:', results.violations);
    }
    return results;
  }
  static async simulateNetworkConditions(page: Page, conditions: {
    offline?: boolean;
    latency?: number;
    downloadThroughput?: number;
    uploadThroughput?: number;
  }) {
    const context = page.context();
    await context.setOffline(conditions.offline || false);
    if (conditions.latency || conditions.downloadThroughput || conditions.uploadThroughput) {
      await context.setGeolocation({ latitude: 0, longitude: 0 });
      await context.setExtraHTTPHeaders({
        'X-Test-Latency': conditions.latency?.toString() || '0'
      });
    }
  }
  static async measurePerformance(page: Page) {
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      return {
        pageLoadTime: navigation.loadEventEnd - navigation.startTime,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.startTime,
        firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
        firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
        resourceCount: performance.getEntriesByType('resource').length,
        memory: (performance as any).memory ? {
          usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
          totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
        } : null
      };
    });
    return metrics;
  }
  static validateHealthcareData(data: any, type: 'patient' | 'appointment' | 'prescription' | 'billing') {
    const validators = {
      patient: {
        required: ['firstName', 'lastName', 'dateOfBirth', 'email', 'phone'],
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        phone: /^\+?[\d\s\-\(\)]+$/,
        dateOfBirth: (date: string) => {
          const d = new Date(date);
          return !isNaN(d.getTime()) && d < new Date();
        }
      },
      appointment: {
        required: ['date', 'time', 'type', 'reason'],
        date: /^\d{4}-\d{2}-\d{2}$/,
        time: /^\d{2}:\d{2}$/
      },
      prescription: {
        required: ['medication', 'dosage', 'frequency', 'duration'],
        dosage: /^\d+(mg|ml|g|mcg)$/i
      },
      billing: {
        required: ['amount', 'description', 'date'],
        amount: (amount: number) => amount > 0,
        date: /^\d{4}-\d{2}-\d{2}$/
      }
    };
    const validator = validators[type];
    const errors: string[] = [];
    validator.required.forEach((field: string) => {
      if (!data[field]) {
        errors.push(`Missing required field: ${field}`);
      }
    });
    Object.entries(validator).forEach(([key, rule]) => {
      if (key !== 'required' && data[key]) {
        if (typeof rule === 'function') {
          if (!rule(data[key])) {
            errors.push(`Invalid format for ${key}`);
          }
        } else if (rule instanceof RegExp) {
          if (!rule.test(data[key])) {
            errors.push(`Invalid format for ${key}`);
          }
        }
      }
    });
    return errors;
  }
}