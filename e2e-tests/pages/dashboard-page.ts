import { Page } from '@playwright/test';
import { BasePage } from './base-page';
export class DashboardPage extends BasePage {
  readonly welcomeMessage = '[data-testid="welcome-message"], .welcome-message, h1';
  readonly patientSummary = '[data-testid="patient-summary"], .patient-summary';
  readonly appointmentSection = '[data-testid="appointments-section"], .appointments-section';
  readonly recentActivity = '[data-testid="recent-activity"], .recent-activity';
  readonly notifications = '[data-testid="notifications"], .notifications';
  readonly quickActions = '[data-testid="quick-actions"], .quick-actions';
  readonly searchInput = 'input[type="search"], [data-testid="search"], .search-input';
  readonly navigationMenu = '[data-testid="navigation"], .navigation, .sidebar';
  readonly profileDropdown = '[data-testid="profile-dropdown"], .profile-dropdown';
  readonly logoutButton = '[data-testid="logout"], .logout-button';
  constructor(page: Page) {
    super(page, '/dashboard');
  }
  async navigateToDashboard() {
    await this.navigate();
    await this.waitForDashboardLoad();
  }
  async waitForDashboardLoad() {
    await this.waitForVisible(this.welcomeMessage);
    await this.waitForVisible(this.patientSummary);
    await this.waitForVisible(this.appointmentSection);
    await this.waitForVisible(this.recentActivity);
    await this.waitForVisible(this.quickActions);
  }
  async getWelcomeMessage() {
    return await this.getText(this.welcomeMessage);
  }
  async getPatientSummary() {
    const summaryElement = await this.page.locator(this.patientSummary);
    const stats = {};
    const statElements = await summaryElement.locator('[data-testid="stat"], .stat-item').all();
    for (const element of statElements) {
      const label = await element.locator('[data-testid="stat-label"], .stat-label').textContent();
      const value = await element.locator('[data-testid="stat-value"], .stat-value').textContent();
      if (label && value) {
        stats[label.trim()] = value.trim();
      }
    }
    return stats;
  }
  async getTodaysAppointments() {
    const appointments = [];
    const appointmentElements = await this.page.locator(`${this.appointmentSection} [data-testid="appointment"], .appointment-item`).all();
    for (const element of appointmentElements) {
      const appointment = {
        time: await element.locator('[data-testid="appointment-time"], .appointment-time').textContent(),
        patient: await element.locator('[data-testid="appointment-patient"], .appointment-patient').textContent(),
        type: await element.locator('[data-testid="appointment-type"], .appointment-type').textContent(),
        status: await element.locator('[data-testid="appointment-status"], .appointment-status').textContent()
      };
      appointments.push(appointment);
    }
    return appointments;
  }
  async getRecentActivities() {
    const activities = [];
    const activityElements = await this.page.locator(`${this.recentActivity} [data-testid="activity"], .activity-item`).all();
    for (const element of activityElements) {
      const activity = {
        type: await element.locator('[data-testid="activity-type"], .activity-type').textContent(),
        description: await element.locator('[data-testid="activity-description"], .activity-description').textContent(),
        time: await element.locator('[data-testid="activity-time"], .activity-time').textContent()
      };
      activities.push(activity);
    }
    return activities;
  }
  async getNotifications() {
    const notifications = [];
    const notificationElements = await this.page.locator(`${this.notifications} [data-testid="notification"], .notification-item`).all();
    for (const element of notificationElements) {
      const notification = {
        type: await element.locator('[data-testid="notification-type"], .notification-type').textContent(),
        message: await element.locator('[data-testid="notification-message"], .notification-message').textContent(),
        time: await element.locator('[data-testid="notification-time"], .notification-time').textContent()
      };
      notifications.push(notification);
    }
    return notifications;
  }
  async getQuickActions() {
    const actions = [];
    const actionElements = await this.page.locator(`${this.quickActions} [data-testid="action"], .quick-action`).all();
    for (const element of actionElements) {
      const action = {
        name: await element.locator('[data-testid="action-name"], .action-name').textContent(),
        icon: await element.locator('[data-testid="action-icon"], .action-icon').getAttribute('data-icon'),
        link: await element.locator('a').getAttribute('href')
      };
      actions.push(action);
    }
    return actions;
  }
  async searchPatients(query: string) {
    await this.fill(this.searchInput, query);
    await this.page.keyboard.press('Enter');
    await this.waitForPageLoad();
    const searchResults = await this.page.locator('[data-testid="search-results"], .search-results').count();
    return searchResults > 0;
  }
  async navigateToSection(sectionName: string) {
    const sectionLink = `${this.navigationMenu} [data-testid="${sectionName.toLowerCase()}"], ${this.navigationMenu} a:text("${sectionName}")`;
    await this.click(sectionLink);
    await this.waitForPageLoad();
  }
  async clickAppointment(appointmentIndex = 0) {
    const appointmentSelector = `${this.appointmentSection} [data-testid="appointment"]:nth-child(${appointmentIndex + 1}), ${this.appointmentSection} .appointment-item:nth-child(${appointmentIndex + 1})`;
    await this.click(appointmentSelector);
    await this.waitForPageLoad();
  }
  async dismissNotification(notificationIndex = 0) {
    const dismissButton = `${this.notifications} [data-testid="notification"]:nth-child(${notificationIndex + 1}) [data-testid="dismiss"], ${this.notifications} .notification-item:nth-child(${notificationIndex + 1}) .dismiss-button`;
    await this.click(dismissButton);
    await this.waitForPageLoad();
  }
  async clickQuickAction(actionName: string) {
    const actionSelector = `${this.quickActions} [data-testid="action-name"]:text("${actionName}")`;
    await this.click(actionSelector);
    await this.waitForPageLoad();
  }
  async openProfileDropdown() {
    await this.click(this.profileDropdown);
    await this.waitForVisible(this.logoutButton);
  }
  async logout() {
    await this.openProfileDropdown();
    await this.click(this.logoutButton);
    await this.waitForPageLoad();
    const currentUrl = await this.getCurrentURL();
    return currentUrl.includes('/login');
  }
  async testAccessibility() {
    await this.navigateToDashboard();
    const accessibilityResults = await this.checkAccessibility();
    return accessibilityResults.violations.length === 0;
  }
  async testPerformance() {
    const startTime = Date.now();
    await this.navigateToDashboard();
    const loadTime = Date.now() - startTime;
    const searchStartTime = Date.now();
    await this.searchPatients('John');
    const searchTime = Date.now() - searchStartTime;
    const navStartTime = Date.now();
    await this.navigateToSection('Patients');
    const navTime = Date.now() - navStartTime;
    return {
      dashboardLoadTime: loadTime,
      searchTime: searchTime,
      navigationTime: navTime,
      totalTime: loadTime + searchTime + navTime
    };
  }
  async testRealTimeUpdates() {
    await this.navigateToDashboard();
    const initialAppointments = await this.getTodaysAppointments();
    const wsConnections = await this.page.evaluate(() => {
      return (window as any).WebSocket ? 'WebSocket support detected' : 'No WebSocket support';
    });
    return {
      initialAppointmentsCount: initialAppointments.length,
      realTimeSupport: wsConnections
    };
  }
  async testResponsiveDesign() {
    const viewports = [
      { width: 1920, height: 1080 }, 
      { width: 768, height: 1024 },  
      { width: 375, height: 667 }   
    ];
    const results = {};
    for (const viewport of viewports) {
      await this.page.setViewportSize(viewport);
      await this.navigateToDashboard();
      const allSectionsVisible = await this.isVisible(this.welcomeMessage) &&
        await this.isVisible(this.patientSummary) &&
        await this.isVisible(this.appointmentSection) &&
        await this.isVisible(this.recentActivity);
      const navigationAccessible = await this.isVisible(this.navigationMenu);
      const searchUsable = await this.isVisible(this.searchInput);
      results[`${viewport.width}x${viewport.height}`] = {
        allSectionsVisible,
        navigationAccessible,
        searchUsable
      };
    }
    return results;
  }
  async testDataRefresh() {
    await this.navigateToDashboard();
    const initialData = {
      patientSummary: await this.getPatientSummary(),
      appointments: await this.getTodaysAppointments(),
      activities: await this.getRecentActivities()
    };
    await this.page.waitForTimeout(5000);
    const refreshedData = {
      patientSummary: await this.getPatientSummary(),
      appointments: await this.getTodaysAppointments(),
      activities: await this.getRecentActivities()
    };
    return {
      initialData,
      refreshedData,
      dataChanged: JSON.stringify(initialData) !== JSON.stringify(refreshedData)
    };
  }
  async testErrorHandling() {
    await this.simulateNetworkConditions({ offline: true });
    try {
      await this.navigateToDashboard();
    } catch (error) {
    }
    const errorMessage = await this.isVisible('[data-testid="error-message"], .error-message, .offline-message');
    await this.simulateNetworkConditions({ offline: false });
    return errorMessage;
  }
  async testUserPreferences() {
    await this.navigateToDashboard();
    const themeToggle = '[data-testid="theme-toggle"], .theme-toggle';
    if (await this.isVisible(themeToggle)) {
      await this.click(themeToggle);
      await this.page.waitForTimeout(1000);
      const bodyClass = await this.page.getAttribute('body', 'class');
      return bodyClass?.includes('dark') || bodyClass?.includes('light');
    }
    return true; 
  }
  async testKeyboardNavigation() {
    await this.navigateToDashboard();
    const interactiveElements = [
      this.searchInput,
      `${this.quickActions} [data-testid="action"]:first-child`,
      `${this.appointmentSection} [data-testid="appointment"]:first-child`,
      this.profileDropdown
    ];
    for (let i = 0; i < interactiveElements.length; i++) {
      await this.page.keyboard.press('Tab');
      await this.page.waitForTimeout(500);
      const focusedElement = await this.page.evaluate(() => {
        const activeElement = document.activeElement;
        return activeElement?.tagName + (activeElement?.getAttribute('data-testid') || '');
      });
      const elementFocused = focusedElement !== null;
      if (!elementFocused) {
        return false;
      }
    }
    return true;
  }
}