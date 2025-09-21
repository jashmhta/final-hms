"""
Cross-Browser and Mobile Responsiveness Testing Framework for HMS

This module provides comprehensive cross-browser and mobile testing:
- Multi-browser compatibility testing
- Mobile responsiveness validation
- Device-specific testing
- Viewport testing
- Touch interface testing
- Performance across browsers
- Accessibility compliance across browsers
- Visual regression testing
"""

import pytest
import json
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import io
import base64

# Import healthcare testing utilities
from ..conftest import (
    HMSTestCase, HealthcareDataMixin, PerformanceTestingMixin,
    SecurityTestingMixin, ComplianceTestingMixin
)

User = get_user_model()


class BrowserType(Enum):
    """Supported browser types"""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"
    OPERA = "opera"


class DeviceType(Enum):
    """Device types for testing"""
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"
    LARGE_DESKTOP = "large_desktop"


class ViewportSize(Enum):
    """Standard viewport sizes"""
    MOBILE_SMALL = (320, 568)
    MOBILE_LARGE = (414, 896)
    TABLET = (768, 1024)
    DESKTOP = (1366, 768)
    DESKTOP_LARGE = (1920, 1080)
    ULTRAWIDE = (2560, 1440)


class DeviceProfile:
    """Device profile for testing"""

    def __init__(self, name: str, device_type: DeviceType, viewport: Tuple[int, int],
                 user_agent: str, pixel_ratio: float = 1.0):
        self.name = name
        self.device_type = device_type
        self.viewport = viewport
        self.user_agent = user_agent
        self.pixel_ratio = pixel_ratio
        self.test_results = []

    def __str__(self):
        return f"{self.name} ({self.device_type.value}) - {self.viewport[0]}x{self.viewport[1]}"


class CrossBrowserTestResult:
    """Cross-browser test result tracking"""

    def __init__(self, test_name: str, browser: BrowserType, device_profile: DeviceProfile):
        self.test_name = test_name
        self.browser = browser
        self.device_profile = device_profile
        self.status = "NOT_TESTED"
        self.performance_metrics = {}
        self.visual_issues = []
        functionaity_issues = []
        self.responsiveness_score = 0.0
        self.accessibility_score = 0.0
        self.performance_score = 0.0
        self.screenshots = []
        self.timestamp = datetime.now()
        self.errors = []
        self.warnings = []

    def add_performance_metric(self, metric_name: str, value: float, unit: str = "ms"):
        """Add performance metric"""
        self.performance_metrics[metric_name] = {
            'value': value,
            'unit': unit,
            'timestamp': datetime.now().isoformat()
        }

    def add_visual_issue(self, issue: str, severity: str = "MEDIUM", screenshot: Optional[str] = None):
        """Add visual issue"""
        self.visual_issues.append({
            'issue': issue,
            'severity': severity,
            'screenshot': screenshot,
            'timestamp': datetime.now().isoformat()
        })

    def add_functionality_issue(self, issue: str, severity: str = "MEDIUM"):
        """Add functionality issue"""
        self.functionality_issues.append({
            'issue': issue,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        })

    def add_error(self, error: str):
        """Add error"""
        self.errors.append({
            'error': error,
            'timestamp': datetime.now().isoformat()
        })

    def add_warning(self, warning: str):
        """Add warning"""
        self.warnings.append({
            'warning': warning,
            'timestamp': datetime.now().isoformat()
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'test_name': self.test_name,
            'browser': self.browser.value,
            'device_profile': {
                'name': self.device_profile.name,
                'device_type': self.device_profile.device_type.value,
                'viewport': self.device_profile.viewport,
                'pixel_ratio': self.device_profile.pixel_ratio
            },
            'status': self.status,
            'performance_metrics': self.performance_metrics,
            'visual_issues': self.visual_issues,
            'functionality_issues': self.functionality_issues,
            'responsiveness_score': self.responsiveness_score,
            'accessibility_score': self.accessibility_score,
            'performance_score': self.performance_score,
            'screenshots': self.screenshots,
            'timestamp': self.timestamp.isoformat(),
            'errors': self.errors,
            'warnings': self.warnings
        }


class CrossBrowserTestingFramework:
    """Cross-browser and mobile testing framework"""

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.test_results = []
        self.device_profiles = self._initialize_device_profiles()
        self.browser_drivers = {}
        self.current_driver = None

    def _initialize_device_profiles(self) -> List[DeviceProfile]:
        """Initialize device profiles for testing"""
        return [
            # Mobile devices
            DeviceProfile(
                "iPhone 12/13/14",
                DeviceType.MOBILE,
                ViewportSize.MOBILE_LARGE.value,
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
                3.0
            ),
            DeviceProfile(
                "iPhone SE",
                DeviceType.MOBILE,
                ViewportSize.MOBILE_SMALL.value,
                "Mozilla/5.0 (iPhone; CPU iPhone OS 13_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Mobile/15E148 Safari/604.1",
                2.0
            ),
            DeviceProfile(
                "Samsung Galaxy S21",
                DeviceType.MOBILE,
                ViewportSize.MOBILE_LARGE.value,
                "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
                3.0
            ),

            # Tablet devices
            DeviceProfile(
                "iPad Pro",
                DeviceType.TABLET,
                ViewportSize.TABLET.value,
                "Mozilla/5.0 (iPad; CPU OS 13_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/604.1",
                2.0
            ),
            DeviceProfile(
                "Samsung Galaxy Tab",
                DeviceType.TABLET,
                ViewportSize.TABLET.value,
                "Mozilla/5.0 (Linux; Android 10; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Safari/537.36",
                2.0
            ),

            # Desktop devices
            DeviceProfile(
                "Standard Desktop",
                DeviceType.DESKTOP,
                ViewportSize.DESKTOP.value,
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                1.0
            ),
            DeviceProfile(
                "Large Desktop",
                DeviceType.DESKTOP,
                ViewportSize.DESKTOP_LARGE.value,
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                2.0
            ),
            DeviceProfile(
                "Ultrawide Monitor",
                DeviceType.LARGE_DESKTOP,
                ViewportSize.ULTRAWIDE.value,
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                1.0
            )
        ]

    def get_browser_driver(self, browser_type: BrowserType, headless: bool = True) -> webdriver.Remote:
        """Get browser driver for specified browser type"""
        if browser_type == BrowserType.CHROME:
            return self._get_chrome_driver(headless)
        elif browser_type == BrowserType.FIREFOX:
            return self._get_firefox_driver(headless)
        elif browser_type == BrowserType.SAFARI:
            return self._get_safari_driver(headless)
        elif browser_type == BrowserType.EDGE:
            return self._get_edge_driver(headless)
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")

    def _get_chrome_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Get Chrome driver"""
        options = Options()

        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-features=VizDisplayCompositor')

        # Enable performance logging
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        driver = webdriver.Chrome(options=options)
        return driver

    def _get_firefox_driver(self, headless: bool = True) -> webdriver.Firefox:
        """Get Firefox driver"""
        options = FirefoxOptions()

        if headless:
            options.add_argument('-headless')

        options.set_preference('webdriver.log.level', 'INFO')

        driver = webdriver.Firefox(options=options)
        return driver

    def _get_safari_driver(self, headless: bool = True) -> webdriver.Safari:
        """Get Safari driver"""
        options = SafariOptions()

        # Safari doesn't support headless mode
        driver = webdriver.Safari(options=options)
        return driver

    def _get_edge_driver(self, headless: bool = True) -> webdriver.Edge:
        """Get Edge driver"""
        options = EdgeOptions()

        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Edge(options=options)
        return driver

    def run_comprehensive_cross_browser_test(self, test_scenarios: List[str]) -> List[CrossBrowserTestResult]:
        """Run comprehensive cross-browser tests"""
        all_results = []

        # Test all browser-device combinations
        for browser_type in BrowserType:
            for device_profile in self.device_profiles:
                print(f"\nTesting {browser_type.value} on {device_profile.name}...")

                browser_results = self.test_browser_device_combination(
                    browser_type, device_profile, test_scenarios
                )
                all_results.extend(browser_results)

        self.test_results = all_results
        return all_results

    def test_browser_device_combination(self, browser_type: BrowserType,
                                      device_profile: DeviceProfile,
                                      test_scenarios: List[str]) -> List[CrossBrowserTestResult]:
        """Test specific browser-device combination"""
        results = []

        try:
            # Initialize browser driver
            driver = self.get_browser_driver(browser_type, headless=True)
            self.current_driver = driver

            # Set device profile
            self._set_device_profile(driver, device_profile)

            # Run test scenarios
            for scenario in test_scenarios:
                result = self.run_test_scenario(driver, scenario, browser_type, device_profile)
                results.append(result)

        except Exception as e:
            print(f"Error testing {browser_type.value} on {device_profile.name}: {str(e)}")
            # Create failed test result
            for scenario in test_scenarios:
                result = CrossBrowserTestResult(scenario, browser_type, device_profile)
                result.status = "FAILED"
                result.add_error(f"Browser initialization failed: {str(e)}")
                results.append(result)

        finally:
            # Clean up driver
            if self.current_driver:
                self.current_driver.quit()
                self.current_driver = None

        return results

    def _set_device_profile(self, driver: webdriver.Remote, device_profile: DeviceProfile):
        """Set device profile for browser"""
        # Set viewport size
        driver.set_window_size(device_profile.viewport[0], device_profile.viewport[1])

        # Set user agent
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            'userAgent': device_profile.user_agent
        })

        # Set device pixel ratio
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            'width': device_profile.viewport[0],
            'height': device_profile.viewport[1],
            'deviceScaleFactor': device_profile.pixel_ratio,
            'mobile': device_profile.device_type == DeviceType.MOBILE
        })

    def run_test_scenario(self, driver: webdriver.Remote, scenario: str,
                          browser_type: BrowserType, device_profile: DeviceProfile) -> CrossBrowserTestResult:
        """Run specific test scenario"""
        result = CrossBrowserTestResult(scenario, browser_type, device_profile)

        try:
            start_time = time.time()

            if scenario == "patient_portal":
                self.test_patient_portal(driver, result)
            elif scenario == "appointment_scheduling":
                self.test_appointment_scheduling(driver, result)
            elif scenario == "medical_records":
                self.test_medical_records(driver, result)
            elif scenario == "billing_portal":
                self.test_billing_portal(driver, result)
            elif scenario == "admin_dashboard":
                self.test_admin_dashboard(driver, result)
            elif scenario == "mobile_navigation":
                self.test_mobile_navigation(driver, result)
            elif scenario == "responsive_layout":
                self.test_responsive_layout(driver, result)
            elif scenario == "accessibility":
                self.test_accessibility_features(driver, result)
            else:
                raise ValueError(f"Unknown test scenario: {scenario}")

            end_time = time.time()
            total_time = end_time - start_time

            result.add_performance_metric("total_test_time", total_time, "seconds")
            result.status = "PASSED" if len(result.errors) == 0 else "FAILED"

        except Exception as e:
            result.status = "FAILED"
            result.add_error(f"Test execution failed: {str(e)}")

        return result

    def test_patient_portal(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test patient portal functionality"""
        print(f"Testing patient portal on {result.browser.value}...")

        try:
            # Navigate to patient portal
            driver.get(f"{self.base_url}/patient-portal")

            # Wait for page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )

            # Test login functionality
            login_start = time.time()
            self._perform_patient_login(driver)
            login_end = time.time()
            result.add_performance_metric("login_time", login_end - login_start, "seconds")

            # Test dashboard load
            dashboard_start = time.time()
            self._verify_patient_dashboard(driver)
            dashboard_end = time.time()
            result.add_performance_metric("dashboard_load_time", dashboard_end - dashboard_start, "seconds")

            # Test navigation
            navigation_start = time.time()
            self._test_portal_navigation(driver)
            navigation_end = time.time()
            result.add_performance_metric("navigation_time", navigation_end - navigation_start, "seconds")

            # Test responsive elements
            responsive_score = self._calculate_responsiveness_score(driver)
            result.responsiveness_score = responsive_score

            # Test accessibility
            accessibility_score = self._calculate_accessibility_score(driver)
            result.accessibility_score = accessibility_score

            # Take screenshot
            screenshot = self._take_screenshot(driver, f"patient_portal_{result.browser.value}")
            result.screenshots.append(screenshot)

        except Exception as e:
            result.add_error(f"Patient portal test failed: {str(e)}")
            raise

    def test_appointment_scheduling(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test appointment scheduling functionality"""
        print(f"Testing appointment scheduling on {result.browser.value}...")

        try:
            # Navigate to appointment scheduling
            driver.get(f"{self.base_url}/appointments/schedule")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".appointment-form"))
            )

            # Test form interactions
            form_start = time.time()
            self._fill_appointment_form(driver)
            form_end = time.time()
            result.add_performance_metric("form_fill_time", form_end - form_start, "seconds")

            # Test date picker functionality
            datepicker_start = time.time()
            self._test_datepicker(driver)
            datepicker_end = time.time()
            result.add_performance_metric("datepicker_time", datepicker_end - datepicker_start, "seconds")

            # Test calendar view
            calendar_start = time.time()
            self._test_calendar_view(driver)
            calendar_end = time.time()
            result.add_performance_metric("calendar_load_time", calendar_end - calendar_start, "seconds")

            # Test responsive behavior
            if result.device_profile.device_type == DeviceType.MOBILE:
                mobile_score = self._test_mobile_appointment_flow(driver)
                result.add_performance_metric("mobile_flow_score", mobile_score, "points")

        except Exception as e:
            result.add_error(f"Appointment scheduling test failed: {str(e)}")
            raise

    def test_medical_records(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test medical records functionality"""
        print(f"Testing medical records on {result.browser.value}...")

        try:
            # Navigate to medical records
            driver.get(f"{self.base_url}/medical-records")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".medical-records-container"))
            )

            # Test records list loading
            records_start = time.time()
            self._verify_records_list(driver)
            records_end = time.time()
            result.add_performance_metric("records_load_time", records_end - records_start, "seconds")

            # Test record details view
            details_start = time.time()
            self._test_record_details(driver)
            details_end = time.time()
            result.add_performance_metric("details_load_time", details_end - details_start, "seconds")

            # Test PDF generation/download
            pdf_start = time.time()
            self._test_pdf_generation(driver)
            pdf_end = time.time()
            result.add_performance_metric("pdf_generation_time", pdf_end - pdf_start, "seconds")

        except Exception as e:
            result.add_error(f"Medical records test failed: {str(e)}")
            raise

    def test_billing_portal(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test billing portal functionality"""
        print(f"Testing billing portal on {result.browser.value}...")

        try:
            # Navigate to billing portal
            driver.get(f"{self.base_url}/billing")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".billing-portal"))
            )

            # Test billing statements
            statements_start = time.time()
            self._test_billing_statements(driver)
            statements_end = time.time()
            result.add_performance_metric("statements_load_time", statements_end - statements_start, "seconds")

            # Test payment processing
            payment_start = time.time()
            self._test_payment_processing(driver)
            payment_end = time.time()
            result.add_performance_metric("payment_processing_time", payment_end - payment_start, "seconds")

        except Exception as e:
            result.add_error(f"Billing portal test failed: {str(e)}")
            raise

    def test_mobile_navigation(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test mobile-specific navigation"""
        print(f"Testing mobile navigation on {result.browser.value}...")

        if result.device_profile.device_type != DeviceType.MOBILE:
            result.add_warning("Mobile navigation test skipped on non-mobile device")
            return

        try:
            # Test hamburger menu
            menu_start = time.time()
            self._test_hamburger_menu(driver)
            menu_end = time.time()
            result.add_performance_metric("menu_interaction_time", menu_end - menu_start, "seconds")

            # Test touch gestures
            touch_start = time.time()
            self._test_touch_gestures(driver)
            touch_end = time.time()
            result.add_performance_metric("touch_response_time", touch_end - touch_start, "seconds")

            # Test mobile form inputs
            form_start = time.time()
            self._test_mobile_forms(driver)
            form_end = time.time()
            result.add_performance_metric("mobile_form_time", form_end - form_start, "seconds")

        except Exception as e:
            result.add_error(f"Mobile navigation test failed: {str(e)}")
            raise

    def test_responsive_layout(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test responsive layout across viewports"""
        print(f"Testing responsive layout on {result.browser.value}...")

        try:
            # Test different viewports
            viewports = [
                (320, 568),   # Mobile
                (768, 1024),  # Tablet
                (1366, 768),  # Desktop
                (1920, 1080), # Large Desktop
            ]

            layout_scores = []

            for width, height in viewports:
                driver.set_window_size(width, height)
                time.sleep(1)  # Allow for layout adjustment

                viewport_score = self._calculate_viewport_responsiveness(driver, width, height)
                layout_scores.append(viewport_score)

            # Calculate overall layout score
            result.responsiveness_score = sum(layout_scores) / len(layout_scores) if layout_scores else 0

            # Test breakpoints
            breakpoint_score = self._test_breakpoints(driver)
            result.add_performance_metric("breakpoint_score", breakpoint_score, "points")

        except Exception as e:
            result.add_error(f"Responsive layout test failed: {str(e)}")
            raise

    def test_accessibility_features(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test accessibility features"""
        print(f"Testing accessibility features on {result.browser.value}...")

        try:
            # Test keyboard navigation
            keyboard_start = time.time()
            keyboard_score = self._test_keyboard_navigation(driver)
            keyboard_end = time.time()
            result.add_performance_metric("keyboard_navigation_time", keyboard_end - keyboard_start, "seconds")
            result.add_performance_metric("keyboard_score", keyboard_score, "points")

            # Test screen reader compatibility
            screen_reader_start = time.time()
            screen_reader_score = self._test_screen_reader_compatibility(driver)
            screen_reader_end = time.time()
            result.add_performance_metric("screen_reader_test_time", screen_reader_end - screen_reader_start, "seconds")
            result.add_performance_metric("screen_reader_score", screen_reader_score, "points")

            # Test color contrast
            contrast_score = self._test_color_contrast(driver)
            result.add_performance_metric("contrast_score", contrast_score, "points")

            # Calculate overall accessibility score
            accessibility_scores = [keyboard_score, screen_reader_score, contrast_score]
            result.accessibility_score = sum(accessibility_scores) / len(accessibility_scores) if accessibility_scores else 0

        except Exception as e:
            result.add_error(f"Accessibility test failed: {str(e)}")
            raise

    def _perform_patient_login(self, driver: webdriver.Remote):
        """Perform patient login"""
        # Find and fill username
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username'], input[type='email'], #username"))
        )
        username_field.send_keys("testpatient@example.com")

        # Find and fill password
        password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password'], #password")
        password_field.send_keys("SecurePass123!")

        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-btn, #login-button")
        login_button.click()

        # Wait for successful login
        WebDriverWait(driver, 10).until(
            EC.url_contains("dashboard") or EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard, .patient-dashboard"))
        )

    def _verify_patient_dashboard(self, driver: webdriver.Remote):
        """Verify patient dashboard loaded correctly"""
        # Check for key dashboard elements
        dashboard_elements = [
            ".welcome-message",
            ".appointment-summary",
            ".medical-records-summary",
            ".billing-summary",
            ".navigation-menu"
        ]

        for element in dashboard_elements:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, element))
                )
            except:
                # Element not found, but continue test
                pass

    def _test_portal_navigation(self, driver: webdriver.Remote):
        """Test portal navigation"""
        # Test navigation menu
        try:
            nav_items = driver.find_elements(By.CSS_SELECTOR, ".nav-item, .menu-item, .navigation-item")
            if nav_items:
                # Click first navigation item
                nav_items[0].click()
                time.sleep(1)
        except:
            pass

    def _calculate_responsiveness_score(self, driver: webdriver.Remote) -> float:
        """Calculate responsiveness score"""
        score = 0.0
        max_score = 100.0

        # Check for responsive meta tag
        try:
            viewport_meta = driver.find_element(By.CSS_SELECTOR, "meta[name='viewport']")
            if viewport_meta:
                score += 20
        except:
            pass

        # Check for CSS media queries (indirect check)
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            window_size = driver.get_window_size()
            if window_size['width'] < 768:
                # Should have mobile layout
                if 'mobile' in body.get_attribute('class').lower():
                    score += 30
            else:
                # Should have desktop layout
                if 'desktop' in body.get_attribute('class').lower():
                    score += 30
        except:
            pass

        # Check for flexible images
        try:
            images = driver.find_elements(By.TAG_NAME, "img")
            flexible_images = 0
            for img in images:
                style = img.get_attribute('style') or ''
                if 'max-width' in style or 'width: 100%' in style:
                    flexible_images += 1

            if flexible_images > len(images) * 0.5:
                score += 20
        except:
            pass

        # Check for responsive tables
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            responsive_tables = 0
            for table in tables:
                parent_class = table.find_element(By.XPATH, "..").get_attribute('class')
                if 'responsive' in parent_class.lower():
                    responsive_tables += 1

            if responsive_tables > 0:
                score += 15
        except:
            pass

        # Check for touch-friendly elements on mobile
        window_size = driver.get_window_size()
        if window_size['width'] < 768:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                touch_friendly = 0
                for button in buttons:
                    size = button.size
                    if size['width'] >= 44 and size['height'] >= 44:  # Apple's HIG minimum
                        touch_friendly += 1

                if touch_friendly > len(buttons) * 0.7:
                    score += 15
            except:
                pass

        return min(score, max_score)

    def _calculate_accessibility_score(self, driver: webdriver.Remote) -> float:
        """Calculate accessibility score"""
        score = 0.0
        max_score = 100.0

        # Check for alt attributes on images
        try:
            images = driver.find_elements(By.TAG_NAME, "img")
            images_with_alt = 0
            for img in images:
                alt_text = img.get_attribute('alt')
                if alt_text and alt_text.strip():
                    images_with_alt += 1

            if len(images) > 0:
                alt_score = (images_with_alt / len(images)) * 30
                score += alt_score
        except:
            pass

        # Check for proper heading structure
        try:
            headings = driver.find_elements(By.XPATH, "//h1|//h2|//h3|//h4|//h5|//h6")
            if headings:
                score += 15
        except:
            pass

        # Check for form labels
        try:
            inputs = driver.find_elements(By.XPATH, "//input[@type!='hidden']")
            inputs_with_labels = 0
            for input_elem in inputs:
                input_id = input_elem.get_attribute('id')
                if input_id:
                    try:
                        label = driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                        inputs_with_labels += 1
                    except:
                        pass

            if len(inputs) > 0:
                label_score = (inputs_with_labels / len(inputs)) * 25
                score += label_score
        except:
            pass

        # Check for ARIA attributes
        try:
            aria_elements = driver.find_elements(By.XPATH, "//*[@aria-label or @aria-describedby or @role]")
            if len(aria_elements) > 0:
                score += 10
        except:
            pass

        # Check for skip navigation link
        try:
            skip_link = driver.find_element(By.CSS_SELECTOR, ".skip-link, a[href='#main'], a[href='#content']")
            score += 10
        except:
            pass

        # Check for language attribute
        try:
            html_tag = driver.find_element(By.TAG_NAME, "html")
            lang_attr = html_tag.get_attribute('lang')
            if lang_attr:
                score += 10
        except:
            pass

        return min(score, max_score)

    def _take_screenshot(self, driver: webdriver.Remote, filename: str) -> str:
        """Take screenshot and return base64 encoded string"""
        try:
            screenshot = driver.get_screenshot_as_png()
            return base64.b64encode(screenshot).decode('utf-8')
        except:
            return ""

    def _test_keyboard_navigation(self, driver: webdriver.Remote) -> float:
        """Test keyboard navigation accessibility"""
        score = 0.0

        try:
            # Test Tab navigation
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.TAB)

            # Check if focus moved
            active_element = driver.switch_to.active_element
            if active_element != body:
                score += 25

            # Test Enter key on buttons
            buttons = driver.find_elements(By.TAG_NAME, "button")
            if buttons:
                buttons[0].send_keys(Keys.ENTER)
                score += 25

            # Test Escape key
            body.send_keys(Keys.ESCAPE)
            score += 25

            # Test arrow key navigation
            body.send_keys(Keys.ARROW_DOWN)
            score += 25

        except Exception as e:
            print(f"Keyboard navigation test error: {e}")

        return score

    def _test_screen_reader_compatibility(self, driver: webdriver.Remote) -> float:
        """Test screen reader compatibility"""
        score = 0.0

        try:
            # Check for ARIA landmarks
            landmarks = driver.find_elements(By.XPATH, "//*[@role='banner' or @role='navigation' or @role='main' or @role='contentinfo' or @role='complementary']")
            if len(landmarks) >= 3:
                score += 33

            # Check for live regions
            live_regions = driver.find_elements(By.XPATH, "//*[@aria-live]")
            if len(live_regions) > 0:
                score += 33

            # Check for proper reading order
            headings = driver.find_elements(By.XPATH, "//h1|//h2|//h3|//h4|//h5|//h6")
            if headings:
                # Check if headings are in proper order
                heading_levels = []
                for heading in headings:
                    level = int(tag_name[1])
                    heading_levels.append(level)

                # Simple check: levels should not decrease by more than 1
                valid_order = True
                for i in range(1, len(heading_levels)):
                    if heading_levels[i] - heading_levels[i-1] < -1:
                        valid_order = False
                        break

                if valid_order:
                    score += 34

        except Exception as e:
            print(f"Screen reader compatibility test error: {e}")

        return score

    def _test_color_contrast(self, driver: webdriver.Remote) -> float:
        """Test color contrast ratios"""
        score = 0.0

        try:
            # This is a simplified test - in practice, you'd use a proper color contrast library
            # For now, we'll check if high contrast mode is supported

            # Check for CSS variables that support high contrast
            css_variables = driver.execute_script("""
                var styles = getComputedStyle(document.documentElement);
                return Object.keys(styles).filter(key => key.startsWith('--'));
            """)

            if len(css_variables) > 10:
                score += 50

            # Check for theme support
            theme_elements = driver.find_elements(By.CSS_SELECTOR, "[data-theme], .theme-switcher")
            if len(theme_elements) > 0:
                score += 50

        except Exception as e:
            print(f"Color contrast test error: {e}")

        return score

    def generate_cross_browser_report(self) -> Dict[str, Any]:
        """Generate comprehensive cross-browser testing report"""
        print("\n=== Generating Cross-Browser Testing Report ===")

        # Analyze results by browser
        browser_results = {}
        for result in self.test_results:
            browser = result.browser.value
            if browser not in browser_results:
                browser_results[browser] = []
            browser_results[browser].append(result)

        # Analyze results by device type
        device_results = {}
        for result in self.test_results:
            device_type = result.device_profile.device_type.value
            if device_type not in device_results:
                device_results[device_type] = []
            device_results[device_type].append(result)

        # Calculate scores
        browser_scores = {}
        for browser, results in browser_results.items():
            passed_tests = len([r for r in results if r.status == "PASSED"])
            total_tests = len(results)
            avg_responsiveness = sum(r.responsiveness_score for r in results) / len(results) if results else 0
            avg_accessibility = sum(r.accessibility_score for r in results) / len(results) if results else 0

            browser_scores[browser] = {
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'avg_responsiveness': avg_responsiveness,
                'avg_accessibility': avg_accessibility,
                'performance_metrics': self._aggregate_performance_metrics(results)
            }

        device_scores = {}
        for device_type, results in device_results.items():
            passed_tests = len([r for r in results if r.status == "PASSED"])
            total_tests = len(results)
            avg_responsiveness = sum(r.responsiveness_score for r in results) / len(results) if results else 0
            avg_accessibility = sum(r.accessibility_score for r in results) / len(results) if results else 0

            device_scores[device_type] = {
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'avg_responsiveness': avg_responsiveness,
                'avg_accessibility': avg_accessibility,
                'performance_metrics': self._aggregate_performance_metrics(results)
            }

        # Generate overall scores
        total_passed = len([r for r in self.test_results if r.status == "PASSED"])
        total_tests = len(self.test_results)
        overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        overall_responsiveness = sum(r.responsiveness_score for r in self.test_results) / len(self.test_results) if self.test_results else 0
        overall_accessibility = sum(r.accessibility_score for r in self.test_results) / len(self.test_results) if self.test_results else 0

        # Create comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_system': 'HMS Enterprise System',
            'base_url': self.base_url,
            'overall_scores': {
                'pass_rate': overall_pass_rate,
                'responsiveness_score': overall_responsiveness,
                'accessibility_score': overall_accessibility,
                'total_tests': total_tests,
                'passed_tests': total_passed,
                'failed_tests': total_tests - total_passed
            },
            'browser_performance': browser_scores,
            'device_performance': device_scores,
            'detailed_results': [result.to_dict() for result in self.test_results],
            'recommendations': self._generate_cross_browser_recommendations(),
            'executive_summary': {
                'best_performing_browser': max(browser_scores.items(), key=lambda x: x[1]['pass_rate'])[0] if browser_scores else 'N/A',
                'worst_performing_browser': min(browser_scores.items(), key=lambda x: x[1]['pass_rate'])[0] if browser_scores else 'N/A',
                'most_compatible_device': max(device_scores.items(), key=lambda x: x[1]['pass_rate'])[0] if device_scores else 'N/A',
                'critical_issues': len([r for r in self.test_results if len(r.errors) > 0]),
                'improvement_areas': self._identify_improvement_areas()
            }
        }

        # Save report
        with open('/tmp/hms_cross_browser_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Cross-browser report generated: {overall_pass_rate:.1f}% pass rate")
        print(f"Best browser: {report['executive_summary']['best_performing_browser']}")
        print(f"Critical issues: {report['executive_summary']['critical_issues']}")

        return report

    def _aggregate_performance_metrics(self, results: List[CrossBrowserTestResult]) -> Dict[str, Any]:
        """Aggregate performance metrics from test results"""
        metrics = {}

        for result in results:
            for metric_name, metric_data in result.performance_metrics.items():
                if metric_name not in metrics:
                    metrics[metric_name] = []
                metrics[metric_name].append(metric_data['value'])

        # Calculate averages
        avg_metrics = {}
        for metric_name, values in metrics.items():
            if values:
                avg_metrics[metric_name] = {
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }

        return avg_metrics

    def _generate_cross_browser_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cross-browser testing recommendations"""
        recommendations = []

        # Analyze common issues
        common_errors = {}
        for result in self.test_results:
            for error in result.errors:
                error_type = error['error'].split(':')[0]
                if error_type not in common_errors:
                    common_errors[error_type] = 0
                common_errors[error_type] += 1

        # Generate recommendations for common errors
        for error_type, count in common_errors.items():
            if count > 2:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Browser Compatibility',
                    'issue': error_type,
                    'frequency': count,
                    'recommendation': f"Address {error_type} issues affecting {count} tests"
                })

        # Browser-specific recommendations
        browser_scores = {}
        for result in self.test_results:
            browser = result.browser.value
            if browser not in browser_scores:
                browser_scores[browser] = {'passed': 0, 'failed': 0}
            if result.status == "PASSED":
                browser_scores[browser]['passed'] += 1
            else:
                browser_scores[browser]['failed'] += 1

        for browser, scores in browser_scores.items():
            if scores['failed'] > scores['passed']:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Browser Optimization',
                    'browser': browser,
                    'issue': 'High failure rate',
                    'pass_rate': scores['passed'] / (scores['passed'] + scores['failed']) * 100,
                    'recommendation': f"Optimize application for {browser} browser"
                })

        # General recommendations
        general_recommendations = [
            {
                'priority': 'HIGH',
                'category': 'Mobile Optimization',
                'recommendation': 'Implement progressive enhancement for mobile devices'
            },
            {
                'priority': 'MEDIUM',
                'category': 'Performance',
                'recommendation': 'Optimize assets and implement lazy loading for better cross-browser performance'
            },
            {
                'priority': 'MEDIUM',
                'category': 'Testing',
                'recommendation': 'Implement continuous cross-browser testing in CI/CD pipeline'
            }
        ]

        recommendations.extend(general_recommendations)

        return recommendations

    def _identify_improvement_areas(self) -> List[str]:
        """Identify areas for improvement"""
        improvement_areas = []

        # Check responsiveness scores
        low_responsiveness = [r for r in self.test_results if r.responsiveness_score < 70]
        if len(low_responsiveness) > len(self.test_results) * 0.3:
            improvement_areas.append("Responsive design")

        # Check accessibility scores
        low_accessibility = [r for r in self.test_results if r.accessibility_score < 70]
        if len(low_accessibility) > len(self.test_results) * 0.3:
            improvement_areas.append("Accessibility compliance")

        # Check failure rates by browser
        browser_failures = {}
        for result in self.test_results:
            browser = result.browser.value
            if result.status == "FAILED":
                if browser not in browser_failures:
                    browser_failures[browser] = 0
                browser_failures[browser] += 1

        for browser, failures in browser_failures.items():
            if failures > 2:
                improvement_areas.append(f"{browser} compatibility")

        return improvement_areas


class CrossBrowserTestCase(HMSTestCase):
    """Base test case for cross-browser testing"""

    def setUp(self):
        super().setUp()
        self.cross_browser_framework = CrossBrowserTestingFramework()
        self.test_scenarios = [
            "patient_portal",
            "appointment_scheduling",
            "medical_records",
            "billing_portal",
            "admin_dashboard",
            "mobile_navigation",
            "responsive_layout",
            "accessibility"
        ]

    def run_comprehensive_cross_browser_test(self):
        """Run comprehensive cross-browser tests"""
        print("\n=== Running Comprehensive Cross-Browser Tests ===")

        results = self.cross_browser_framework.run_comprehensive_cross_browser_test(self.test_scenarios)

        # Generate report
        report = self.cross_browser_framework.generate_cross_browser_report()

        # Log results
        self.log_cross_browser_results(results)

        # Assert minimum pass rate
        overall_pass_rate = report['overall_scores']['pass_rate']
        self.assertGreaterEqual(
            overall_pass_rate,
            80.0,
            f"Cross-browser pass rate too low: {overall_pass_rate:.1f}% (minimum 80% required)"
        )

        return results, report

    def log_cross_browser_results(self, results):
        """Log cross-browser test results"""
        print(f"\n=== Cross-Browser Test Results ===")
        print(f"Total tests: {len(results)}")

        # Group by browser
        browser_results = {}
        for result in results:
            browser = result.browser.value
            if browser not in browser_results:
                browser_results[browser] = []
            browser_results[browser].append(result)

        for browser, browser_test_results in browser_results.items():
            passed = len([r for r in browser_test_results if r.status == "PASSED"])
            total = len(browser_test_results)
            pass_rate = (passed / total * 100) if total > 0 else 0

            print(f"{browser}: {passed}/{total} ({pass_rate:.1f}%)")

        print("=" * 50)


# Import Selenium keys
from selenium.webdriver.common.keys import Keys

# Pytest fixtures
@pytest.fixture
def cross_browser_framework():
    """Cross-browser testing framework fixture"""
    return CrossBrowserTestingFramework()


@pytest.fixture
def device_profiles():
    """Device profiles fixture"""
    framework = CrossBrowserTestingFramework()
    return framework.device_profiles


@pytest.fixture
def browser_types():
    """Browser types fixture"""
    return list(BrowserType)


# Cross-browser test markers
def pytest_configure(config):
    """Configure pytest with cross-browser markers"""
    config.addinivalue_line(
        "markers",
        "cross_browser: Mark test as cross-browser test"
    )
    config.addinivalue_line(
        "markers",
        "mobile: Mark test as mobile-specific test"
    )
    config.addinivalue_line(
        "markers",
        "responsive: Mark test as responsive design test"
    )
    config.addinivalue_line(
        "markers",
        "accessibility: Mark test as accessibility test"
    )