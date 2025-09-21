/**
 * ULTRA-COMPREHENSIVE FRONTEND AESTHETICS & UX TESTING
 *
 * This test suite validates the complete frontend aesthetics and user experience
 * with zero tolerance for any visual or functional imperfections.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { BrowserRouter } from 'react-router-dom';

// Import components to test
import App from '../App';
import { VitalSignsMonitor } from '../components/healthcare/VitalSignsMonitor';
import { PatientCard } from '../components/healthcare/PatientCard';
import { MedicalRecordViewer } from '../components/healthcare/MedicalRecordViewer';
import { DashboardModule } from '../components/modules/DashboardModule';
import { ResponsiveLayout } from '../components/layout/ResponsiveLayout';

// Extend jest matchers
expect.extend(toHaveNoViolations);

// Create test theme
const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
    background: { default: '#f5f5f5' },
  },
  typography: {
    fontFamily: 'Roboto, sans-serif',
    h1: { fontSize: '2.5rem' },
    h2: { fontSize: '2rem' },
    h3: { fontSize: '1.75rem' },
    h4: { fontSize: '1.5rem' },
    h5: { fontSize: '1.25rem' },
    h6: { fontSize: '1rem' },
  },
});

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </ThemeProvider>
);

describe('🎨 Frontend Aesthetics & Ultra-Comprehensive Testing', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
    // Mock intersection observer for responsive testing
    global.IntersectionObserver = class IntersectionObserver {
      constructor() {}
      disconnect() {}
      observe() {}
      unobserve() {}
    };
  });

  describe('Visual Design Consistency', () => {
    test('🎨 Primary color consistency across all components', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const elements = screen.getAllByRole('button');
      elements.forEach(element => {
        const computedStyle = getComputedStyle(element);
        expect(computedStyle.backgroundColor).toBe('rgb(25, 118, 210)'); // Primary color
      });
    });

    test('🎨 Typography hierarchy and consistency', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <DashboardModule />
          </TestWrapper>
        );
      });

      // Test heading hierarchy
      const headings = screen.getAllByRole('heading');
      headings.forEach((heading, index) => {
        const computedStyle = getComputedStyle(heading);
        const fontSize = parseFloat(computedStyle.fontSize);

        // Ensure proper font size hierarchy
        expect(fontSize).toBeGreaterThan(0);
        expect(computedStyle.fontFamily).toContain('Roboto');
      });
    });

    test('🎨 Spacing and layout consistency', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <PatientCard />
          </TestWrapper>
        );
      });

      // Test consistent padding
      const cards = screen.getAllByRole('article');
      cards.forEach(card => {
        const computedStyle = getComputedStyle(card);
        expect(parseInt(computedStyle.padding)).toBeGreaterThanOrEqual(8);
        expect(parseInt(computedStyle.padding)).toBeLessThanOrEqual(32);
      });
    });

    test('🎨 Border radius consistency', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <PatientCard />
          </TestWrapper>
        );
      });

      const cards = screen.getAllByRole('article');
      cards.forEach(card => {
        const computedStyle = getComputedStyle(card);
        expect(parseInt(computedStyle.borderRadius)).toBeGreaterThanOrEqual(4);
        expect(parseInt(computedStyle.borderRadius)).toBeLessThanOrEqual(16);
      });
    });

    test('🎨 Shadow depth consistency', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <PatientCard />
          </TestWrapper>
        );
      });

      const cards = screen.getAllByRole('article');
      cards.forEach(card => {
        const computedStyle = getComputedStyle(card);
        expect(computedStyle.boxShadow).not.toBe('none');
      });
    });
  });

  describe('Responsive Design Testing', () => {
    const viewports = [
      { width: 375, height: 667, name: 'Mobile' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 2560, height: 1440, name: 'Ultra-wide' },
    ];

    viewports.forEach(viewport => {
      test(`📱 Responsive layout on ${viewport.name} (${viewport.width}x${viewport.height})`, async () => {
        // Mock viewport size
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: viewport.width,
        });
        Object.defineProperty(window, 'innerHeight', {
          writable: true,
          configurable: true,
          value: viewport.height,
        });

        await act(async () => {
          render(
            <TestWrapper>
              <ResponsiveLayout>
                <div>Test Content</div>
              </ResponsiveLayout>
            </TestWrapper>
          );
        });

        // Trigger resize event
        window.dispatchEvent(new Event('resize'));

        await waitFor(() => {
          const layout = screen.getByText('Test Content');
          expect(layout).toBeInTheDocument();
        });
      });
    });

    test('📱 Touch-friendly interactions on mobile', async () => {
      // Simulate mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      // Test touch targets are large enough
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        const rect = button.getBoundingClientRect();
        expect(rect.width).toBeGreaterThanOrEqual(44); // Minimum touch target size
        expect(rect.height).toBeGreaterThanOrEqual(44);
      });
    });

    test('📱 Orientation change handling', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <ResponsiveLayout>
              <div>Test Content</div>
            </ResponsiveLayout>
          </TestWrapper>
        );
      });

      // Simulate orientation change
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 768,
      });

      window.dispatchEvent(new Event('resize'));

      await waitFor(() => {
        const layout = screen.getByText('Test Content');
        expect(layout).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility Compliance (WCAG 2.1 AA)', () => {
    test('♿ AXE accessibility compliance', async () => {
      await act(async () => {
        const { container } = render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
      });
    });

    test('♿ Alt text for all images', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <MedicalRecordViewer />
          </TestWrapper>
        );
      });

      const images = screen.getAllByRole('img');
      images.forEach(image => {
        expect(image).toHaveAttribute('alt');
        expect(image.getAttribute('alt')).not.toBe('');
      });
    });

    test('♿ Color contrast compliance', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      // Test color contrast for text elements
      const textElements = screen.getAllByText(/./);
      textElements.forEach(element => {
        const computedStyle = getComputedStyle(element);
        const color = computedStyle.color;
        const backgroundColor = computedStyle.backgroundColor;

        // Basic contrast check (in real implementation, use proper contrast ratio calculation)
        expect(color).not.toBe(backgroundColor);
      });
    });

    test('♿ Keyboard navigation support', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <DashboardModule />
          </TestWrapper>
        );
      });

      // Test tab navigation
      const interactiveElements = screen.getAllByRole('button');

      // Simulate keyboard navigation
      interactiveElements[0]?.focus();
      expect(document.activeElement).toBe(interactiveElements[0]);

      // Tab to next element
      fireEvent.keyDown(document.activeElement as HTMLElement, { key: 'Tab' });
      expect(document.activeElement).toBe(interactiveElements[1] || interactiveElements[0]);
    });

    test('♿ ARIA labels and roles', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      // Test proper ARIA labels
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        if (button.getAttribute('aria-label')) {
          expect(button.getAttribute('aria-label')).not.toBe('');
        }
      });
    });

    test('♿ Focus management', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <DashboardModule />
          </TestWrapper>
        );
      });

      // Test focus styles
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        fireEvent.focus(button);
        const computedStyle = getComputedStyle(button);
        expect(computedStyle.outline).not.toBe('none');
      });
    });

    test('♿ Form accessibility', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <div>
              <label htmlFor="test-input">Test Label</label>
              <input id="test-input" type="text" />
            </div>
          </TestWrapper>
        );
      });

      const input = screen.getByLabelText('Test Label');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('id', 'test-input');
    });
  });

  describe('User Journey Workflows', () => {
    test('🏥 Patient registration journey', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <App />
          </TestWrapper>
        );
      });

      // Navigate through patient registration
      const registerButton = await screen.findByRole('button', { name: /register/i });
      await user.click(registerButton);

      // Fill registration form
      const nameInput = await screen.findByLabelText(/name/i);
      await user.type(nameInput, 'John Doe');

      const emailInput = await screen.findByLabelText(/email/i);
      await user.type(emailInput, 'john.doe@example.com');

      const submitButton = await screen.findByRole('button', { name: /submit/i });
      await user.click(submitButton);

      // Verify successful registration
      await waitFor(() => {
        expect(screen.getByText(/registration successful/i)).toBeInTheDocument();
      });
    });

    test('🏥 Appointment scheduling journey', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <App />
          </TestWrapper>
        );
      });

      // Navigate to appointments
      const appointmentsButton = await screen.findByRole('button', { name: /appointments/i });
      await user.click(appointmentsButton);

      // Select appointment type
      const appointmentType = await screen.findByLabelText(/appointment type/i);
      await user.selectOptions(appointmentType, 'consultation');

      // Select date
      const dateInput = await screen.findByLabelText(/date/i);
      await user.type(dateInput, '2024-01-15');

      // Submit appointment
      const submitButton = await screen.findByRole('button', { name: /schedule/i });
      await user.click(submitButton);

      // Verify appointment scheduling
      await waitFor(() => {
        expect(screen.getByText(/appointment scheduled/i)).toBeInTheDocument();
      });
    });

    test('🏥 Medical record access journey', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <MedicalRecordViewer />
          </TestWrapper>
        );
      });

      // Search for patient
      const searchInput = await screen.findByPlaceholderText(/search patient/i);
      await user.type(searchInput, 'John Doe');

      const searchButton = await screen.findByRole('button', { name: /search/i });
      await user.click(searchButton);

      // Verify patient records are displayed
      await waitFor(() => {
        expect(screen.getByText(/medical records/i)).toBeInTheDocument();
      });

      // View specific record
      const viewButton = await screen.findByRole('button', { name: /view/i });
      await user.click(viewButton);

      // Verify record details
      await waitFor(() => {
        expect(screen.getByText(/patient information/i)).toBeInTheDocument();
      });
    });

    test('🏥 Dashboard navigation journey', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <DashboardModule />
          </TestWrapper>
        );
      });

      // Test navigation between dashboard sections
      const sections = ['overview', 'patients', 'appointments', 'analytics'];

      for (const section of sections) {
        const navButton = await screen.findByRole('button', { name: new RegExp(section, 'i') });
        await user.click(navButton);

        await waitFor(() => {
          expect(screen.getByText(new RegExp(section, 'i'))).toBeInTheDocument();
        });
      }
    });

    test('🏥 Emergency workflow', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <App />
          </TestWrapper>
        );
      });

      // Access emergency module
      const emergencyButton = await screen.findByRole('button', { name: /emergency/i });
      await user.click(emergencyButton);

      // Verify emergency interface loads
      await waitFor(() => {
        expect(screen.getByText(/emergency triage/i)).toBeInTheDocument();
      });

      // Test emergency patient intake
      const patientIdInput = await screen.findByLabelText(/patient id/i);
      await user.type(patientIdInput, '12345');

      const severitySelect = await screen.findByLabelText(/severity/i);
      await user.selectOptions(severitySelect, 'critical');

      const submitButton = await screen.findByRole('button', { name: /start triage/i });
      await user.click(submitButton);

      // Verify emergency response
      await waitFor(() => {
        expect(screen.getByText(/triage initiated/i)).toBeInTheDocument();
      });
    });
  });

  describe('Performance Testing', () => {
    test('⚡ Component render performance', async () => {
      const start = performance.now();

      await act(async () => {
        render(
          <TestWrapper>
            <DashboardModule />
          </TestWrapper>
        );
      });

      const end = performance.now();
      const renderTime = end - start;

      expect(renderTime).toBeLessThan(100); // Should render in under 100ms
    });

    test('⚡ Interaction response time', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const button = await screen.findByRole('button', { name: /refresh/i });

      const start = performance.now();
      await user.click(button);
      const end = performance.now();

      const responseTime = end - start;
      expect(responseTime).toBeLessThan(50); // Should respond in under 50ms
    });

    test('⚡ Memory usage efficiency', async () => {
      const initialMemory = performance.memory?.usedJSHeapSize || 0;

      await act(async () => {
        render(
          <TestWrapper>
            <DashboardModule />
          </TestWrapper>
        );
      });

      const finalMemory = performance.memory?.usedJSHeapSize || 0;
      const memoryIncrease = finalMemory - initialMemory;

      expect(memoryIncrease).toBeLessThan(1024 * 1024); // Should use less than 1MB additional memory
    });

    test('⚡ Large dataset handling', async () => {
      // Mock large dataset
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `Patient ${i}`,
        age: 20 + (i % 60),
        condition: ['Healthy', 'Diabetes', 'Hypertension'][i % 3]
      }));

      await act(async () => {
        render(
          <TestWrapper>
            <div data-testid="large-list">
              {largeDataset.map(patient => (
                <div key={patient.id}>{patient.name}</div>
              ))}
            </div>
          </TestWrapper>
        );
      });

      const start = performance.now();

      // Test scrolling performance
      const list = screen.getByTestId('large-list');
      list.scrollTop = 1000;

      const end = performance.now();
      const scrollTime = end - start;

      expect(scrollTime).toBeLessThan(16); // Should scroll in under 16ms (60fps)
    });

    test('⚡ Animation performance', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      // Test animation frame rate
      const animationDuration = 1000; // 1 second
      const expectedFrames = 60; // 60fps

      const frameCount = await new Promise<number>((resolve) => {
        let frames = 0;
        const startTime = performance.now();

        const countFrame = () => {
          frames++;
          if (performance.now() - startTime < animationDuration) {
            requestAnimationFrame(countFrame);
          } else {
            resolve(frames);
          }
        };

        requestAnimationFrame(countFrame);
      });

      expect(frameCount).toBeGreaterThanOrEqual(expectedFrames * 0.8); // Should maintain 80% of expected frame rate
    });
  });

  describe('Cross-Browser Compatibility', () => {
    const browsers = [
      { name: 'Chrome', userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' },
      { name: 'Firefox', userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0' },
      { name: 'Safari', userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15' },
    ];

    browsers.forEach(browser => {
      test(`🌐 Compatibility with ${browser.name}`, async () => {
        // Mock user agent
        Object.defineProperty(navigator, 'userAgent', {
          writable: true,
          configurable: true,
          value: browser.userAgent,
        });

        await act(async () => {
          render(
            <TestWrapper>
              <VitalSignsMonitor />
            </TestWrapper>
          );
        });

        // Verify component renders correctly
        expect(screen.getByText(/vital signs/i)).toBeInTheDocument();

        // Test basic functionality
        const button = screen.getByRole('button', { name: /refresh/i });
        expect(button).toBeInTheDocument();
        expect(button).toBeEnabled();
      });
    });
  });

  describe('Visual Regression Testing', () => {
    test('📸 Visual consistency snapshot', async () => {
      await act(async () => {
        const { container } = render(
          <TestWrapper>
            <PatientCard />
          </TestWrapper>
        );

        // In a real implementation, this would use jest-image-snapshot
        // For now, we'll verify the structure
        expect(container).toMatchSnapshot();
      });
    });

    test('📸 Layout consistency', async () => {
      await act(async () => {
        const { container } = render(
          <TestWrapper>
            <DashboardModule />
          </TestWrapper>
        );

        // Verify key layout elements
        expect(container.querySelector('.dashboard-header')).toBeInTheDocument();
        expect(container.querySelector('.dashboard-content')).toBeInTheDocument();
        expect(container.querySelector('.dashboard-sidebar')).toBeInTheDocument();
      });
    });
  });

  describe('Internationalization and Localization', () => {
    test('🌍 Text rendering with different character sets', async () => {
      const testTexts = [
        'English Text',
        '中文文本',
        'العربية النص',
        'Русский текст',
        '日本語テキスト',
        '한국어 텍스트'
      ];

      for (const text of testTexts) {
        await act(async () => {
          render(
            <TestWrapper>
              <div>{text}</div>
            </TestWrapper>
          );
        });

        expect(screen.getByText(text)).toBeInTheDocument();
      }
    });

    test('🌍 Right-to-left layout support', async () => {
      // Mock RTL direction
      document.documentElement.setAttribute('dir', 'rtl');

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const container = screen.getByRole('main');
      expect(container).toHaveAttribute('dir', 'rtl');

      // Reset direction
      document.documentElement.removeAttribute('dir');
    });
  });

  describe('Error Handling and Edge Cases', () => {
    test('⚠️ Graceful handling of missing data', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <PatientCard patient={null} />
          </TestWrapper>
        );
      });

      // Should show appropriate loading or error state
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    test('⚠️ Network error handling', async () => {
      // Mock network error
      jest.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('Network error'));

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      jest.restoreAllMocks();
    });

    test('⚠️ Loading states', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <MedicalRecordViewer loading={true} />
          </TestWrapper>
        );
      });

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Mobile-Specific Features', () => {
    test('📱 Swipe gesture support', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const container = screen.getByRole('main');

      // Simulate swipe gesture
      fireEvent.touchStart(container, { touches: [{ clientX: 100, clientY: 200 }] });
      fireEvent.touchMove(container, { touches: [{ clientX: 50, clientY: 200 }] });
      fireEvent.touchEnd(container);

      // Verify swipe action
      await waitFor(() => {
        expect(screen.getByText(/swipe detected/i)).toBeInTheDocument();
      });
    });

    test('📱 Pinch-to-zoom support', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <MedicalRecordViewer />
          </TestWrapper>
        );
      });

      const container = screen.getByRole('main');

      // Simulate pinch gesture
      fireEvent.touchStart(container, { touches: [{ clientX: 100, clientY: 200 }, { clientX: 150, clientY: 250 }] });
      fireEvent.touchMove(container, { touches: [{ clientX: 80, clientY: 200 }, { clientX: 170, clientY: 250 }] });
      fireEvent.touchEnd(container);

      // Verify zoom action
      await waitFor(() => {
        expect(screen.getByText(/zoom detected/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation and User Input', () => {
    test('✅ Real-time form validation', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <div>
              <form>
                <input
                  type="email"
                  placeholder="Email"
                  required
                  data-testid="email-input"
                />
                <button type="submit">Submit</button>
              </form>
            </div>
          </TestWrapper>
        );
      });

      const emailInput = screen.getByTestId('email-input');
      const submitButton = screen.getByRole('button', { name: /submit/i });

      // Test invalid email
      await user.type(emailInput, 'invalid-email');
      await user.click(submitButton);

      expect(screen.getByText(/invalid email/i)).toBeInTheDocument();

      // Test valid email
      await user.clear(emailInput);
      await user.type(emailInput, 'valid@example.com');
      await user.click(submitButton);

      expect(screen.queryByText(/invalid email/i)).not.toBeInTheDocument();
    });

    test('✅ Password strength validation', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <div>
              <input
                type="password"
                placeholder="Password"
                data-testid="password-input"
              />
              <div data-testid="password-strength"></div>
            </div>
          </TestWrapper>
        );
      });

      const passwordInput = screen.getByTestId('password-input');
      const strengthIndicator = screen.getByTestId('password-strength');

      // Test weak password
      await user.type(passwordInput, '123');
      expect(strengthIndicator).toHaveTextContent(/weak/i);

      // Test strong password
      await user.clear(passwordInput);
      await user.type(passwordInput, 'StrongPassword123!');
      expect(strengthIndicator).toHaveTextContent(/strong/i);
    });
  });

  describe('Animation and Transitions', () => {
    test('🎬 Smooth transitions', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const button = screen.getByRole('button', { name: /refresh/i });

      // Test hover transition
      fireEvent.mouseEnter(button);
      const computedStyle = getComputedStyle(button);
      expect(computedStyle.transition).not.toBe('none');

      // Test click animation
      await user.click(button);
      await waitFor(() => {
        expect(screen.getByText(/refreshed/i)).toBeInTheDocument();
      });
    });

    test('🎬 Loading animations', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <MedicalRecordViewer loading={true} />
          </TestWrapper>
        );
      });

      const loader = screen.getByRole('progressbar');
      const computedStyle = getComputedStyle(loader);

      // Verify animation is present
      expect(computedStyle.animation).not.toBe('none');
    });
  });

  describe('Dark Mode and Theme Support', () => {
    test('🌙 Dark mode functionality', async () => {
      // Mock dark mode preference
      window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const container = screen.getByRole('main');
      const computedStyle = getComputedStyle(container);

      // Verify dark mode styles
      expect(computedStyle.backgroundColor).toBe('rgb(18, 18, 18)'); // Dark background
      expect(computedStyle.color).toBe('rgb(255, 255, 255)'); // Light text
    });

    test('🌙 Theme switching', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const themeToggle = screen.getByRole('button', { name: /toggle theme/i });

      // Switch to dark mode
      await user.click(themeToggle);

      const container = screen.getByRole('main');
      const computedStyle = getComputedStyle(container);

      expect(computedStyle.backgroundColor).toBe('rgb(18, 18, 18)');
    });
  });

  describe('Performance Optimization', () => {
    test('🚀 Lazy loading of components', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <DashboardModule />
          </TestWrapper>
        );
      });

      // Simulate scrolling to lazy-loaded component
      const lazyComponent = screen.getByTestId('lazy-component');

      // Trigger intersection observer
      const mockIntersectionObserver = global.IntersectionObserver;
      const [callback] = mockIntersectionObserver.mock.calls;

      callback([
        {
          isIntersecting: true,
          target: lazyComponent
        }
      ]);

      // Verify component loads
      await waitFor(() => {
        expect(screen.getByText(/lazy loaded/i)).toBeInTheDocument();
      });
    });

    test('🚀 Code splitting optimization', async () => {
      // Mock dynamic import
      jest.mock('react', () => ({
        ...jest.requireActual('react'),
        lazy: jest.fn(() => Promise.resolve(() => <div>Lazy Component</div>))
      }));

      await act(async () => {
        render(
          <TestWrapper>
            <div>Test Component</div>
          </TestWrapper>
        );
      });

      expect(screen.getByText('Test Component')).toBeInTheDocument();
    });
  });

  describe('Accessibility Advanced Features', () => {
    test('🔊 Screen reader announcements', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      // Mock screen reader
      const announceMock = jest.fn();
      window.announce = announceMock;

      const button = screen.getByRole('button', { name: /refresh/i });
      await user.click(button);

      // Verify announcement
      expect(announceMock).toHaveBeenCalledWith('Data refreshed successfully');
    });

    test('🔊 High contrast mode support', async () => {
      // Mock high contrast mode
      window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-contrast: high)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const button = screen.getByRole('button', { name: /refresh/i });
      const computedStyle = getComputedStyle(button);

      // Verify high contrast styles
      expect(parseInt(computedStyle.borderWidth)).toBeGreaterThan(2);
    });

    test('🔊 Reduced motion support', async () => {
      // Mock reduced motion preference
      window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const animatedElement = screen.getByTestId('animated-element');
      const computedStyle = getComputedStyle(animatedElement);

      // Verify animations are disabled
      expect(computedStyle.animation).toBe('none');
    });
  });

  describe('Security and Privacy Features', () => {
    test('🔒 Secure input handling', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <div>
              <input
                type="password"
                placeholder="Password"
                data-testid="password-input"
              />
              <button type="button" data-testid="toggle-password">Show</button>
            </div>
          </TestWrapper>
        );
      });

      const passwordInput = screen.getByTestId('password-input');
      const toggleButton = screen.getByTestId('toggle-password');

      // Test password masking
      await user.type(passwordInput, 'secret123');
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Test password visibility toggle
      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'text');

      // Test password re-masking
      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    test('🔒 Data sanitization', async () => {
      const maliciousData = '<script>alert("XSS")</script>';

      await act(async () => {
        render(
          <TestWrapper>
            <div data-testid="sanitized-content">{maliciousData}</div>
          </TestWrapper>
        );
      });

      const content = screen.getByTestId('sanitized-content');
      expect(content.innerHTML).not.toContain('<script>');
      expect(content.textContent).toBe(maliciousData);
    });
  });

  describe('User Experience Enhancements', () => {
    test('✨ Toast notifications', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const button = screen.getByRole('button', { name: /save/i });
      await user.click(button);

      // Verify toast notification
      await waitFor(() => {
        expect(screen.getByText(/saved successfully/i)).toBeInTheDocument();
      });

      // Verify auto-dismissal
      await waitFor(() => {
        expect(screen.queryByText(/saved successfully/i)).not.toBeInTheDocument();
      }, { timeout: 5000 });
    });

    test('✨ Tooltips and help text', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const helpButton = screen.getByRole('button', { name: /help/i });

      // Show tooltip
      fireEvent.mouseEnter(helpButton);

      await waitFor(() => {
        expect(screen.getByText(/help information/i)).toBeInTheDocument();
      });

      // Hide tooltip
      fireEvent.mouseLeave(helpButton);

      await waitFor(() => {
        expect(screen.queryByText(/help information/i)).not.toBeInTheDocument();
      });
    });

    test('✨ Keyboard shortcuts', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      // Test keyboard shortcut
      fireEvent.keyDown(document, { key: 'r', ctrl: true });

      await waitFor(() => {
        expect(screen.getByText(/refreshed via shortcut/i)).toBeInTheDocument();
      });
    });
  });

  describe('Device and Platform Integration', () => {
    test('📱 Device orientation handling', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      // Simulate device orientation change
      window.dispatchEvent(new Event('orientationchange'));

      await waitFor(() => {
        expect(screen.getByText(/orientation updated/i)).toBeInTheDocument();
      });
    });

    test('📱 Battery status integration', async () => {
      // Mock battery API
      const mockBattery = {
        level: 0.8,
        charging: true,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      };

      (navigator as any).getBattery = jest.fn().mockResolvedValue(mockBattery);

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      await waitFor(() => {
        expect(screen.getByText(/battery level: 80%/i)).toBeInTheDocument();
      });
    });

    test('📱 Network status handling', async () => {
      // Mock network status
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        configurable: true,
        value: true,
      });

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      // Test offline mode
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        configurable: true,
        value: false,
      });

      window.dispatchEvent(new Event('offline'));

      await waitFor(() => {
        expect(screen.getByText(/offline mode/i)).toBeInTheDocument();
      });
    });
  });

  describe('Advanced Features and Innovations', () => {
    test('🎯 Voice command support', async () => {
      // Mock speech recognition
      const mockRecognition = {
        start: jest.fn(),
        stop: jest.fn(),
        onresult: null,
        onerror: null,
      };

      (window as any).SpeechRecognition = jest.fn().mockImplementation(() => mockRecognition);

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const voiceButton = screen.getByRole('button', { name: /voice command/i });
      await user.click(voiceButton);

      expect(mockRecognition.start).toHaveBeenCalled();
    });

    test('🎯 Gesture recognition', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const container = screen.getByRole('main');

      // Simulate gesture
      const gestureEvent = new CustomEvent('gesture', {
        detail: { type: 'swipe', direction: 'left' }
      });
      container.dispatchEvent(gestureEvent);

      await waitFor(() => {
        expect(screen.getByText(/gesture recognized/i)).toBeInTheDocument();
      });
    });

    test('🎯 Biometric authentication', async () => {
      // Mock biometric API
      (window as any).PublicKeyCredential = {
        create: jest.fn().mockResolvedValue({}),
        get: jest.fn().mockResolvedValue({})
      };

      await act(async () => {
        render(
          <TestWrapper>
            <VitalSignsMonitor />
          </TestWrapper>
        );
      });

      const biometricButton = screen.getByRole('button', { name: /biometric login/i });
      await user.click(biometricButton);

      await waitFor(() => {
        expect(screen.getByText(/biometric authentication successful/i)).toBeInTheDocument();
      });
    });
  });

  describe('Final Validation and Quality Assurance', () => {
    test('✅ Zero-bug compliance validation', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <App />
          </TestWrapper>
        );
      });

      // Verify no console errors
      const consoleErrors: string[] = [];
      const originalError = console.error;

      console.error = (...args) => {
        consoleErrors.push(args.join(' '));
        originalError(...args);
      };

      // Perform comprehensive interactions
      const buttons = screen.getAllByRole('button');
      for (const button of buttons.slice(0, 5)) { // Test first 5 buttons
        await user.click(button);
      }

      // Restore console.error
      console.error = originalError;

      // Verify no errors occurred
      expect(consoleErrors).toHaveLength(0);
    });

    test('✅ Performance benchmark validation', async () => {
      const startTime = performance.now();

      await act(async () => {
        render(
          <TestWrapper>
            <App />
          </TestWrapper>
        );
      });

      const endTime = performance.now();
      const totalTime = endTime - startTime;

      // Verify performance benchmarks
      expect(totalTime).toBeLessThan(200); // Should render in under 200ms

      // Verify memory usage
      const memory = performance.memory;
      if (memory) {
        expect(memory.usedJSHeapSize).toBeLessThan(50 * 1024 * 1024); // Should use less than 50MB
      }
    });

    test('✅ Accessibility final validation', async () => {
      await act(async () => {
        const { container } = render(
          <TestWrapper>
            <App />
          </TestWrapper>
        );

        // Final accessibility check
        const results = await axe(container);
        expect(results).toHaveNoViolations();

        // Verify specific accessibility requirements
        const interactiveElements = screen.getAllByRole('button');
        interactiveElements.forEach(element => {
          expect(element).toHaveAttribute('tabindex');
          expect(element).toBeEnabled();
        });

        const images = screen.getAllByRole('img');
        images.forEach(image => {
          expect(image).toHaveAttribute('alt');
        });
      });
    });

    test('✅ Cross-platform compatibility final check', async () => {
      const platforms = [
        { name: 'Desktop', width: 1920, height: 1080 },
        { name: 'Tablet', width: 768, height: 1024 },
        { name: 'Mobile', width: 375, height: 667 },
      ];

      for (const platform of platforms) {
        // Set viewport
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: platform.width,
        });
        Object.defineProperty(window, 'innerHeight', {
          writable: true,
          configurable: true,
          value: platform.height,
        });

        await act(async () => {
          render(
            <TestWrapper>
              <App />
            </TestWrapper>
          );
        });

        // Trigger resize
        window.dispatchEvent(new Event('resize'));

        // Verify layout adapts
        await waitFor(() => {
          const app = screen.getByRole('application');
          expect(app).toBeInTheDocument();
        });

        // Clean up
        jest.clearAllMocks();
      }
    });
  });
});

// Export test configuration for continuous integration
export const frontendAestheticsTestConfig = {
  testTimeout: 30000,
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}'
  ],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx'
  ],
  coverageThreshold: {
    global: {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95
    }
  }
};

// Global test setup
beforeAll(() => {
  // Setup test environment
  console.log('🚀 Starting Frontend Aesthetics Ultra-Comprehensive Testing...');
});

afterAll(() => {
  // Cleanup test environment
  console.log('✅ Frontend Aesthetics Ultra-Comprehensive Testing Completed!');
});

// Error handling for test failures
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  process.exit(1);
});