import { Page, expect } from '@playwright/test';
import { TestHelpers } from '../utils/test-helpers';
export class BasePage {
  readonly page: Page;
  readonly url: string;
  constructor(page: Page, url: string) {
    this.page = page;
    this.url = url;
  }
  async navigate() {
    await this.page.goto(this.url);
    await this.waitForPageLoad();
  }
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForLoadState('domcontentloaded');
    await TestHelpers.waitForLoadingComplete(this.page);
  }
  async takeScreenshot(name: string) {
    await TestHelpers.takeScreenshot(this.page, name);
  }
  async isVisible(selector: string, timeout = 5000) {
    try {
      await this.page.waitForSelector(selector, { state: 'visible', timeout });
      return true;
    } catch {
      return false;
    }
  }
  async waitForVisible(selector: string, timeout = 10000) {
    await this.page.waitForSelector(selector, { state: 'visible', timeout });
  }
  async waitForHidden(selector: string, timeout = 10000) {
    await this.page.waitForSelector(selector, { state: 'hidden', timeout });
  }
  async click(selector: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    await this.page.click(selector);
  }
  async fill(selector: string, value: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    await this.page.fill(selector, value);
  }
  async selectOption(selector: string, value: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    await this.page.selectOption(selector, value);
  }
  async check(selector: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    await this.page.check(selector);
  }
  async uncheck(selector: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    await this.page.uncheck(selector);
  }
  async getText(selector: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    return await this.page.textContent(selector);
  }
  async getElementCount(selector: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    return await this.page.locator(selector).count();
  }
  async containsText(selector: string, text: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    await expect(this.page.locator(selector)).toContainText(text);
  }
  async waitForSuccess(timeout = 10000) {
    await TestHelpers.waitForSuccess(this.page, timeout);
  }
  async waitForAPIResponse(urlPattern: string, timeout = 30000) {
    return await TestHelpers.waitForAPIResponse(this.page, urlPattern, timeout);
  }
  async checkAccessibility() {
    return await TestHelpers.checkAccessibility(this.page);
  }
  async measurePerformance() {
    return await TestHelpers.measurePerformance(this.page);
  }
  async simulateNetworkConditions(conditions: any) {
    await TestHelpers.simulateNetworkConditions(this.page, conditions);
  }
  async validatePageTitle(expectedTitle: string) {
    await expect(this.page).toHaveTitle(new RegExp(expectedTitle));
  }
  async validateURLContains(path: string) {
    await expect(this.page).toHaveURL(new RegExp(path));
  }
  async getCurrentURL() {
    return this.page.url();
  }
  async refresh() {
    await this.page.reload();
    await this.waitForPageLoad();
  }
  async goBack() {
    await this.page.goBack();
    await this.waitForPageLoad();
  }
  async goForward() {
    await this.page.goForward();
    await this.waitForPageLoad();
  }
  async switchToFrame(selector: string, timeout = 10000) {
    const frame = await this.page.frameLocator(selector);
    await frame.locator('body').waitFor({ state: 'visible', timeout });
    return frame;
  }
  async switchToMainFrame() {
  }
  async handleDialog(type: 'accept' | 'dismiss' = 'accept') {
    this.page.on('dialog', async dialog => {
      if (type === 'accept') {
        await dialog.accept();
      } else {
        await dialog.dismiss();
      }
    });
  }
  getConsoleMessages() {
    const messages: string[] = [];
    this.page.on('console', msg => {
      messages.push(msg.text());
    });
    return messages;
  }
  getPageErrors() {
    const errors: Error[] = [];
    this.page.on('pageerror', error => {
      errors.push(error);
    });
    return errors;
  }
  async waitForEnabled(selector: string, timeout = 10000) {
    await this.page.waitForSelector(selector, { state: 'enabled', timeout });
  }
  async waitForDisabled(selector: string, timeout = 10000) {
    await this.page.waitForSelector(selector, { state: 'disabled', timeout });
  }
  async hover(selector: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    await this.page.hover(selector);
  }
  async dragAndDrop(source: string, target: string, timeout = 10000) {
    await this.waitForVisible(source, timeout);
    await this.waitForVisible(target, timeout);
    await this.page.dragAndDrop(source, target);
  }
  async uploadFile(selector: string, filePath: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    await this.page.setInputFiles(selector, filePath);
  }
  async getAttribute(selector: string, attributeName: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    return await this.page.getAttribute(selector, attributeName);
  }
  async hasClass(selector: string, className: string, timeout = 10000) {
    await this.waitForVisible(selector, timeout);
    const classes = await this.page.getAttribute(selector, 'class');
    return classes?.includes(className) || false;
  }
}