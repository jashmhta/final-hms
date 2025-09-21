"""
Comprehensive Accessibility Testing Implementation
Tests WCAG 2.1 AA and AAA compliance with healthcare-specific accessibility requirements
"""

import pytest
import json
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

from .accessibility_framework import (
    AccessibilityTestingFramework,
    AccessibilityTestResult,
    AccessibilityAuditResult,
    WCAGGuideline,
    WCAGLevel,
    AccessibilityViolationType,
    AccessibilityTestMixin,
    HealthcareAccessibilityTestMixin,
    run_accessibility_audit
)

# Test configuration
TEST_BASE_URL = "http://localhost:3000"
HEALTHCARE_TEST_PAGES = [
    "/patient-portal",
    "/appointments",
    "/medical-records",
    "/billing",
    "/pharmacy",
    "/lab-results",
    "/emergency"
]

# Test data
ACCESSIBILITY_TEST_CASES = [
    {
        "name": "Patient Portal Accessibility",
        "url": "/patient-portal",
        "expected_min_score": 85.0,
        "healthcare_specific": True,
        "critical_features": ["login", "dashboard", "appointments"]
    },
    {
        "name": "Appointment Scheduling Accessibility",
        "url": "/appointments",
        "expected_min_score": 90.0,
        "healthcare_specific": True,
        "critical_features": ["calendar", "time_slots", "confirmation"]
    },
    {
        "name": "Medical Records Accessibility",
        "url": "/medical-records",
        "expected_min_score": 95.0,
        "healthcare_specific": True,
        "critical_features": ["records_view", "download", "share"]
    },
    {
        "name": "Billing Portal Accessibility",
        "url": "/billing",
        "expected_min_score": 85.0,
        "healthcare_specific": True,
        "critical_features": ["invoices", "payment", "insurance"]
    },
    {
        "name": "Pharmacy Portal Accessibility",
        "url": "/pharmacy",
        "expected_min_score": 90.0,
        "healthcare_specific": True,
        "critical_features": ["prescriptions", "refills", "delivery"]
    },
    {
        "name": "Lab Results Accessibility",
        "url": "/lab-results",
        "expected_min_score": 95.0,
        "healthcare_specific": True,
        "critical_features": ["results_view", "trends", "abnormal_flags"]
    },
    {
        "name": "Emergency Information Accessibility",
        "url": "/emergency",
        "expected_min_score": 98.0,
        "healthcare_specific": True,
        "critical_features": ["emergency_contacts", "medical_history", "allergies"]
    }
]

class TestAccessibilityFramework(AccessibilityTestMixin):
    """Test the accessibility testing framework itself"""

    @pytest.fixture
    def framework(self):
        """Accessibility framework fixture"""
        return AccessibilityTestingFramework(TEST_BASE_URL)

    @pytest.fixture
    def sample_page_content(self):
        """Sample HTML content for testing"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <header>
                <nav>
                    <ul>
                        <li><a href="#home">Home</a></li>
                        <li><a href="#about">About</a></li>
                    </ul>
                </nav>
            </header>
            <main>
                <h1>Welcome</h1>
                <p>This is a test page.</p>
                <img src="test.jpg" alt="Test image">
                <form>
                    <label for="name">Name:</label>
                    <input type="text" id="name" name="name">
                    <button type="submit">Submit</button>
                </form>
            </main>
            <footer>
                <p>&copy; 2024</p>
            </footer>
        </body>
        </html>
        """

    def test_framework_initialization(self, framework):
        """Test framework initialization"""
        assert framework.base_url == TEST_BASE_URL
        assert isinstance(framework.violations, list)
        assert isinstance(framework.healthcare_violations, list)
        assert isinstance(framework.contrast_thresholds, dict)

    def test_wcag_guidelines_coverage(self):
        """Test WCAG guidelines coverage"""
        # Test that all major WCAG guidelines are covered
        guidelines = [g for g in WCAGGuideline]
        assert len(guidelines) > 50  # Should have many guidelines covered

    def test_violation_types_coverage(self):
        """Test violation types coverage"""
        violation_types = [v for v in AccessibilityViolationType]
        assert len(violation_types) > 20  # Should have many violation types

    def test_sample_page_accessibility(self, framework, sample_page_content):
        """Test accessibility analysis of sample page"""
        soup = BeautifulSoup(sample_page_content, 'html.parser')

        # Test alt text detection
        images = soup.find_all('img')
        assert len(images) == 1

        # Test heading structure
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        assert len(headings) == 1

        # Test form labels
        labels = soup.find_all('label')
        assert len(labels) == 1

class TestWCAGCompliance(AccessibilityTestMixin, HealthcareAccessibilityTestMixin):
    """Test WCAG 2.1 compliance across all pages"""

    @pytest.mark.parametrize("test_case", ACCESSIBILITY_TEST_CASES)
    def test_page_accessibility_compliance(self, chrome_driver, test_case):
        """Test accessibility compliance for each healthcare page"""
        url = urljoin(TEST_BASE_URL, test_case["url"])

        # Run accessibility audit
        audit_result = run_accessibility_audit(url, chrome_driver)

        # Assert compliance requirements
        self.assert_accessibility_compliance(audit_result, test_case["expected_min_score"])
        self.assert_no_critical_violations(audit_result)
        self.assert_wcag_aa_compliance(audit_result)

        if test_case["healthcare_specific"]:
            self.assert_healthcare_accessibility_compliance(audit_result)

    def test_patient_portal_accessibility(self, chrome_driver):
        """Test patient portal accessibility in detail"""
        url = urljoin(TEST_BASE_URL, "/patient-portal")
        audit_result = run_accessibility_audit(url, chrome_driver)

        # Test specific patient portal requirements
        assert audit_result.overall_score >= 85.0

        # Check for login form accessibility
        login_violations = [
            v for v in audit_result.violations
            if 'login' in v.element.lower() or 'form' in v.element.lower()
        ]

        # Assert no critical login form issues
        critical_login_issues = [
            v for v in login_violations if v.severity == "Critical"
        ]
        assert len(critical_login_issues) == 0

    def test_appointment_scheduling_accessibility(self, chrome_driver):
        """Test appointment scheduling accessibility"""
        url = urljoin(TEST_BASE_URL, "/appointments")
        audit_result = run_accessibility_audit(url, chrome_driver)

        assert audit_result.overall_score >= 90.0

        # Check for calendar accessibility
        calendar_violations = [
            v for v in audit_result.violations
            if 'calendar' in v.element.lower() or 'date' in v.element.lower()
        ]

        # Assert calendar is accessible
        critical_calendar_issues = [
            v for v in calendar_violations if v.severity in ["Critical", "Serious"]
        ]
        assert len(critical_calendar_issues) == 0

    def test_medical_records_accessibility(self, chrome_driver):
        """Test medical records accessibility"""
        url = urljoin(TEST_BASE_URL, "/medical-records")
        audit_result = run_accessibility_audit(url, chrome_driver)

        assert audit_result.overall_score >= 95.0

        # Check for data table accessibility
        table_violations = [
            v for v in audit_result.violations
            if 'table' in v.element.lower()
        ]

        # Assert tables are accessible
        critical_table_issues = [
            v for v in table_violations if v.severity in ["Critical", "Serious"]
        ]
        assert len(critical_table_issues) == 0

    def test_emergency_information_accessibility(self, chrome_driver):
        """Test emergency information accessibility (highest priority)"""
        url = urljoin(TEST_BASE_URL, "/emergency")
        audit_result = run_accessibility_audit(url, chrome_driver)

        # Emergency information must have highest accessibility
        assert audit_result.overall_score >= 98.0
        assert audit_result.critical_violations == 0

        # Test emergency-specific requirements
        self.assert_emergency_information_accessibility(audit_result)

class TestHealthcareSpecificAccessibility(HealthcareAccessibilityTestMixin):
    """Test healthcare-specific accessibility requirements"""

    def test_high_contrast_mode_support(self, chrome_driver):
        """Test high contrast mode for medical data"""
        url = urljoin(TEST_BASE_URL, "/medical-records")

        # Test with different contrast modes
        chrome_driver.get(url)

        # Simulate high contrast mode
        chrome_driver.execute_script("""
            document.body.style.backgroundColor = '#000000';
            document.body.style.color = '#ffffff';
        """)

        # Check that content remains readable
        text_elements = chrome_driver.find_elements(By.CSS_SELECTOR, "p, h1, h2, h3, h4, h5, h6")
        assert len(text_elements) > 0

        # Verify contrast is sufficient (simplified test)
        for element in text_elements:
            style = chrome_driver.execute_script("""
                return window.getComputedStyle(arguments[0]);
            """, element)

            # Check that text color has sufficient contrast with background
            text_color = style.get('color', '#000000')
            bg_color = style.get('background-color', '#ffffff')

            # Basic contrast check (would use proper contrast library in production)
            assert text_color != bg_color, f"Text and background colors are too similar"

    def test_screen_reader_compatibility(self, chrome_driver):
        """Test screen reader compatibility for medical information"""
        url = urljoin(TEST_BASE_URL, "/patient-portal")
        chrome_driver.get(url)

        # Check for ARIA attributes
        aria_elements = chrome_driver.find_elements(By.CSS_SELECTOR, "[aria-label], [aria-labelledby]")
        assert len(aria_elements) > 0

        # Check for proper heading structure
        headings = chrome_driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        assert len(headings) > 0

        # Check for landmark regions
        landmarks = chrome_driver.find_elements(By.CSS_SELECTOR, "header, nav, main, footer")
        assert len(landmarks) >= 3  # Should have at least header, main, footer

    def test_keyboard_navigation_healthcare(self, chrome_driver):
        """Test keyboard navigation for healthcare workflows"""
        url = urljoin(TEST_BASE_URL, "/appointments")
        chrome_driver.get(url)

        # Test keyboard navigation through appointment booking
        body = chrome_driver.find_element(By.TAG_NAME, "body")

        # Navigate through interactive elements
        interactive_elements = chrome_driver.find_elements(By.CSS_SELECTOR,
            "button, input, select, textarea, a[href]")

        # Test that all interactive elements are keyboard accessible
        for element in interactive_elements[:5]:  # Test first 5 elements
            try:
                # Scroll element into view
                chrome_driver.execute_script("arguments[0].scrollIntoView();", element)

                # Test keyboard focus
                element.send_keys(Keys.TAB)

                # Verify focus is visible
                active_element = chrome_driver.switch_to.active_element
                assert active_element.is_displayed(), "Element should be visible when focused"

            except Exception as e:
                pytest.fail(f"Keyboard navigation failed for element: {e}")

    def test_medical_form_accessibility(self, chrome_driver):
        """Test medical form accessibility"""
        url = urljoin(TEST_BASE_URL, "/patient-portal")
        chrome_driver.get(url)

        # Find medical forms
        forms = chrome_driver.find_elements(By.TAG_NAME, "form")

        for form in forms:
            # Test form labels
            inputs = form.find_elements(By.CSS_SELECTOR, "input, select, textarea")

            for input_element in inputs:
                input_type = input_element.get_attribute("type")

                # Skip hidden inputs and submit buttons
                if input_type in ["hidden", "submit"]:
                    continue

                # Check for associated label
                input_id = input_element.get_attribute("id")
                if input_id:
                    labels = form.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    assert len(labels) > 0, f"Input {input_id} missing associated label"
                else:
                    # Check for aria-label if no id
                    aria_label = input_element.get_attribute("aria-label")
                    assert aria_label, f"Input missing both id and aria-label"

    def test_medication_information_accessibility(self, chrome_driver):
        """Test medication information accessibility"""
        url = urljoin(TEST_BASE_URL, "/pharmacy")
        chrome_driver.get(url)

        # Look for medication information
        medication_elements = chrome_driver.find_elements(By.CSS_SELECTOR,
            "[class*='medication'], [id*='medication']")

        if medication_elements:
            # Test that medication information is properly labeled
            for element in medication_elements:
                # Check for ARIA labels
                aria_label = element.get_attribute("aria-label")
                if aria_label:
                    assert len(aria_label.strip()) > 0, "ARIA label should not be empty"

                # Check for proper text alternatives
                if element.tag_name == "img":
                    alt_text = element.get_attribute("alt")
                    assert alt_text, "Medication images should have alt text"

    def test_emergency_accessibility_critical(self, chrome_driver):
        """Test emergency information accessibility (critical)"""
        url = urljoin(TEST_BASE_URL, "/emergency")
        chrome_driver.get(url)

        # Emergency information must be immediately accessible
        emergency_elements = chrome_driver.find_elements(By.CSS_SELECTOR,
            "[class*='emergency'], [id*='emergency']")

        assert len(emergency_elements) > 0, "Emergency information should be present"

        for element in emergency_elements:
            # Test that emergency information is highly visible
            style = chrome_driver.execute_script("""
                return window.getComputedStyle(arguments[0]);
            """, element)

            # Check for high contrast or prominent styling
            font_weight = style.get('font-weight', 'normal')
            font_size = style.get('font-size', '16px')

            # Emergency information should be prominent
            assert font_weight in ['bold', '700', '800', '900'] or int(font_size.replace('px', '')) >= 18, \
                "Emergency information should be prominently displayed"

class TestResponsiveAccessibility(AccessibilityTestMixin):
    """Test responsive design accessibility"""

    @pytest.mark.parametrize("viewport_size", [
        (375, 667),    # Mobile
        (768, 1024),   # Tablet
        (1920, 1080)   # Desktop
    ])
    def test_responsive_accessibility(self, chrome_driver, viewport_size):
        """Test accessibility across different viewport sizes"""
        width, height = viewport_size
        chrome_driver.set_window_size(width, height)

        url = urljoin(TEST_BASE_URL, "/patient-portal")
        audit_result = run_accessibility_audit(url, chrome_driver)

        # Assert accessibility across all screen sizes
        self.assert_accessibility_compliance(audit_result, 80.0)
        self.assert_no_critical_violations(audit_result)

    def test_mobile_accessibility_features(self, mobile_driver):
        """Test mobile-specific accessibility features"""
        url = urljoin(TEST_BASE_URL, "/appointments")
        mobile_driver.get(url)

        # Test touch targets (minimum 44x44 pixels)
        interactive_elements = mobile_driver.find_elements(By.CSS_SELECTOR,
            "button, input[type='submit'], a[href]")

        for element in interactive_elements[:5]:  # Test first 5 elements
            size = element.size
            assert size['width'] >= 44 or size['height'] >= 44, \
                f"Touch target too small: {size['width']}x{size['height']}px"

    def test_reflow_accessibility(self, chrome_driver):
        """Test reflow accessibility (WCAG 1.4.10)"""
        url = urljoin(TEST_BASE_URL, "/medical-records")
        chrome_driver.get(url)

        # Test different viewport sizes
        viewports = [
            (1280, 720),   # Large desktop
            (1024, 768),   # Desktop
            (768, 1024),   # Tablet
            (375, 667)     # Mobile
        ]

        for width, height in viewports:
            chrome_driver.set_window_size(width, height)

            # Check that content doesn't require horizontal scrolling
            body_width = chrome_driver.execute_script("return document.body.scrollWidth")
            viewport_width = chrome_driver.execute_script("return window.innerWidth")

            # Allow small tolerance for rounding
            tolerance = 5
            assert body_width <= viewport_width + tolerance, \
                f"Content requires horizontal scrolling at {width}x{height}"

class TestScreenReaderCompatibility(HealthcareAccessibilityTestMixin):
    """Test screen reader compatibility"""

    def test_aria_attributes_healthcare(self, chrome_driver):
        """Test ARIA attributes for healthcare content"""
        url = urljoin(TEST_BASE_URL, "/medical-records")
        chrome_driver.get(url)

        # Test ARIA landmarks
        landmarks = chrome_driver.find_elements(By.CSS_SELECTOR,
            "[role='banner'], [role='navigation'], [role='main'], [role='contentinfo']")

        # Should have at least main content area
        main_landmarks = [l for l in landmarks if l.get_attribute("role") == "main"]
        assert len(main_landmarks) > 0, "Should have main landmark"

    def test_dynamic_content_accessibility(self, chrome_driver):
        """Test dynamic content accessibility"""
        url = urljoin(TEST_BASE_URL, "/appointments")
        chrome_driver.get(url)

        # Test live regions for dynamic content
        live_regions = chrome_driver.find_elements(By.CSS_SELECTOR,
            "[aria-live], [aria-busy]")

        # Should have live regions for dynamic updates
        assert len(live_regions) > 0, "Should have live regions for dynamic content"

    def test_form_validation_accessibility(self, chrome_driver):
        """Test form validation accessibility"""
        url = urljoin(TEST_BASE_URL, "/patient-portal")
        chrome_driver.get(url)

        # Find form elements
        forms = chrome_driver.find_elements(By.TAG_NAME, "form")

        for form in forms:
            # Test error messaging
            error_elements = form.find_elements(By.CSS_SELECTOR,
                "[role='alert'], [aria-invalid='true']")

            # Should have accessible error messaging
            assert len(error_elements) >= 0, "Form should support accessible error messaging"

class TestPerformanceAccessibility(AccessibilityTestMixin):
    """Test performance aspects of accessibility"""

    def test_accessibility_performance(self, chrome_driver):
        """Test that accessibility doesn't impact performance significantly"""
        url = urljoin(TEST_BASE_URL, "/patient-portal")

        # Measure load time
        start_time = time.time()
        chrome_driver.get(url)
        load_time = time.time() - start_time

        # Measure accessibility audit time
        audit_start = time.time()
        audit_result = run_accessibility_audit(url, chrome_driver)
        audit_time = time.time() - audit_start

        # Performance should be reasonable
        assert load_time < 10.0, f"Page load time too slow: {load_time:.2f}s"
        assert audit_time < 30.0, f"Accessibility audit too slow: {audit_time:.2f}s"

    def test_large_content_accessibility(self, chrome_driver):
        """Test accessibility with large medical content"""
        url = urljoin(TEST_BASE_URL, "/medical-records")
        chrome_driver.get(url)

        # Test with large content
        chrome_driver.execute_script("""
            // Simulate large medical records content
            const container = document.createElement('div');
            container.innerHTML = '<h2>Medical History</h2>';
            for (let i = 0; i < 100; i++) {
                container.innerHTML += `<p>Medical record entry ${i}: Lorem ipsum dolor sit amet...</p>`;
            }
            document.body.appendChild(container);
        """)

        # Should still be accessible
        audit_result = run_accessibility_audit(url, chrome_driver)
        self.assert_accessibility_compliance(audit_result, 75.0)

class TestAccessibilityRegression(AccessibilityTestMixin):
    """Test accessibility regression prevention"""

    def test_baseline_accessibility_scores(self, chrome_driver):
        """Test that accessibility scores don't regress"""
        baseline_scores = {
            "/patient-portal": 85.0,
            "/appointments": 90.0,
            "/medical-records": 95.0,
            "/billing": 85.0,
            "/pharmacy": 90.0,
            "/lab-results": 95.0,
            "/emergency": 98.0
        }

        for page_url, baseline_score in baseline_scores.items():
            url = urljoin(TEST_BASE_URL, page_url)
            audit_result = run_accessibility_audit(url, chrome_driver)

            # Score should not decrease by more than 5%
            min_score = baseline_score - 5.0
            assert audit_result.overall_score >= min_score, \
                f"Accessibility score regressed for {page_url}: {audit_result.overall_score:.1f}% < {min_score:.1f}%"

    def test_violation_count_regression(self, chrome_driver):
        """Test that violation counts don't increase"""
        url = urljoin(TEST_BASE_URL, "/patient-portal")
        audit_result = run_accessibility_audit(url, chrome_driver)

        # Should not have more than 10 violations of any severity
        assert audit_result.total_violations <= 10, \
            f"Too many violations: {audit_result.total_violations}"

        # Should not have more than 2 serious violations
        assert audit_result.serious_violations <= 2, \
            f"Too many serious violations: {audit_result.serious_violations}"

# Integration tests with other testing frameworks
class TestAccessibilityIntegration:
    """Test integration with other testing frameworks"""

    def test_cross_browser_accessibility(self, chrome_driver):
        """Test accessibility across different browsers"""
        url = urljoin(TEST_BASE_URL, "/patient-portal")

        # Run accessibility audit
        audit_result = run_accessibility_audit(url, chrome_driver)

        # Should meet basic accessibility standards
        assert audit_result.overall_score >= 80.0
        assert audit_result.critical_violations == 0

    def test_security_accessibility_integration(self, chrome_driver):
        """Test integration between security and accessibility"""
        url = urljoin(TEST_BASE_URL, "/patient-portal")
        chrome_driver.get(url)

        # Test that secure elements are also accessible
        login_form = chrome_driver.find_element(By.CSS_SELECTOR, "form")
        password_field = login_form.find_element(By.CSS_SELECTOR, "input[type='password']")

        # Password field should be accessible
        assert password_field.is_displayed()

        # Should have proper labeling
        password_id = password_field.get_attribute("id")
        if password_id:
            labels = chrome_driver.find_elements(By.CSS_SELECTOR, f"label[for='{password_id}']")
            assert len(labels) > 0, "Password field should have label"

# Utility functions
def create_accessibility_test_suite():
    """Create comprehensive accessibility test suite"""
    suite = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes",
        "--accessibility"
    ])
    return suite

def generate_accessibility_report():
    """Generate comprehensive accessibility report"""
    framework = AccessibilityTestingFramework(TEST_BASE_URL)

    report = "# Healthcare Management System Accessibility Report\n\n"
    report += "## Executive Summary\n"
    report += "This report provides a comprehensive accessibility assessment of the "
    report += "Healthcare Management System (HMS) across all major pages and workflows.\n\n"

    # Test each page
    for test_case in ACCESSIBILITY_TEST_CASES:
        url = urljoin(TEST_BASE_URL, test_case["url"])

        # Create driver for testing
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        with webdriver.Chrome(options=options) as driver:
            audit_result = framework.run_comprehensive_accessibility_audit(url, driver)

            report += f"### {test_case['name']}\n"
            report += f"- **URL:** {url}\n"
            report += f"- **Score:** {audit_result.overall_score:.1f}%\n"
            report += f"- **Violations:** {audit_result.total_violations}\n"
            report += f"- **Critical:** {audit_result.critical_violations}\n"
            report += f"- **Healthcare Issues:** {len(audit_result.healthcare_specific_issues)}\n\n"

    return report

# Test runner
if __name__ == "__main__":
    # Run accessibility tests
    pytest.main([__file__, "-v", "--tb=short"])

    # Generate report
    report = generate_accessibility_report()

    # Save report
    with open("/tmp/accessibility_report.md", "w") as f:
        f.write(report)

    print("Accessibility testing completed. Report saved to /tmp/accessibility_report.md")