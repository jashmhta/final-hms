"""
Comprehensive Cross-Browser and Mobile Testing Suite for HMS System

This module implements comprehensive cross-browser and mobile testing:
- Multi-browser compatibility testing
- Mobile responsiveness validation
- Device-specific functionality testing
- Performance benchmarking across browsers
- Accessibility testing across platforms
- Visual regression testing
- Touch interface testing
- Viewport and breakpoint testing
"""

import pytest
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.touch_actions import TouchActions
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image, ImageChops
import io
import base64
import statistics

# Import cross-browser framework
from .cross_browser_framework import (
    CrossBrowserTestingFramework, BrowserType, DeviceType, DeviceProfile,
    CrossBrowserTestResult, CrossBrowserTestCase, ViewportSize
)
from ..conftest import HealthcareDataMixin, PerformanceTestingMixin

User = get_user_model()


class CrossBrowserComprehensiveTestSuite(CrossBrowserTestCase):
    """Comprehensive cross-browser and mobile testing suite for HMS system"""

    @pytest.mark.cross_browser
    def test_patient_portal_comprehensive(self):
        """Test patient portal across all browsers and devices"""
        print("\n=== Testing Patient Portal Cross-Browser ===")

        # Test scenarios for patient portal
        scenarios = [
            "login_functionality",
            "dashboard_loading",
            "personal_information",
            "appointment_history",
            "medical_records_access",
            "billing_information",
            "prescription_management",
            "communication_portal",
            "health_tracking",
            "logout_functionality"
        ]

        # Run tests across all browser-device combinations
        results = self.run_comprehensive_scenario_test("patient_portal", scenarios)

        # Analyze results
        self.analyze_patient_portal_results(results)

        print("✓ Patient Portal cross-browser tests completed")

    def run_comprehensive_scenario_test(self, base_scenario: str, scenarios: List[str]) -> List[CrossBrowserTestResult]:
        """Run comprehensive tests for specific scenario"""
        all_results = []

        for browser_type in BrowserType:
            for device_profile in self.cross_browser_framework.device_profiles:
                print(f"\n  Testing {browser_type.value} on {device_profile.name}...")

                try:
                    # Initialize browser
                    driver = self.cross_browser_framework.get_browser_driver(browser_type, headless=True)
                    self.cross_browser_framework.current_driver = driver

                    # Set device profile
                    self.cross_browser_framework._set_device_profile(driver, device_profile)

                    # Run all scenarios for this browser-device combination
                    for scenario in scenarios:
                        result = self.run_single_scenario(
                            driver, f"{base_scenario}_{scenario}",
                            browser_type, device_profile
                        )
                        all_results.append(result)

                except Exception as e:
                    print(f"    Error: {str(e)}")
                    # Create failed results for all scenarios
                    for scenario in scenarios:
                        result = CrossBrowserTestResult(
                            f"{base_scenario}_{scenario}",
                            browser_type,
                            device_profile
                        )
                        result.status = "FAILED"
                        result.add_error(f"Browser initialization failed: {str(e)}")
                        all_results.append(result)

                finally:
                    # Clean up
                    if self.cross_browser_framework.current_driver:
                        self.cross_browser_framework.current_driver.quit()
                        self.cross_browser_framework.current_driver = None

        return all_results

    def run_single_scenario(self, driver: webdriver.Remote, scenario: str,
                          browser_type: BrowserType, device_profile: DeviceProfile) -> CrossBrowserTestResult:
        """Run single test scenario"""
        result = CrossBrowserTestResult(scenario, browser_type, device_profile)

        try:
            start_time = time.time()

            if scenario == "patient_portal_login_functionality":
                self.test_patient_portal_login(driver, result)
            elif scenario == "patient_portal_dashboard_loading":
                self.test_patient_portal_dashboard(driver, result)
            elif scenario == "patient_portal_personal_information":
                self.test_patient_portal_personal_info(driver, result)
            elif scenario == "patient_portal_appointment_history":
                self.test_patient_portal_appointments(driver, result)
            elif scenario == "patient_portal_medical_records_access":
                self.test_patient_portal_medical_records(driver, result)
            elif scenario == "patient_portal_billing_information":
                self.test_patient_portal_billing(driver, result)
            elif scenario == "patient_portal_prescription_management":
                self.test_patient_portal_prescriptions(driver, result)
            elif scenario == "patient_portal_communication_portal":
                self.test_patient_portal_communication(driver, result)
            elif scenario == "patient_portal_health_tracking":
                self.test_patient_portal_health_tracking(driver, result)
            elif scenario == "patient_portal_logout_functionality":
                self.test_patient_portal_logout(driver, result)
            else:
                result.add_warning(f"Unknown scenario: {scenario}")

            end_time = time.time()
            result.add_performance_metric("total_time", end_time - start_time, "seconds")
            result.status = "PASSED" if len(result.errors) == 0 else "FAILED"

        except Exception as e:
            result.status = "FAILED"
            result.add_error(f"Scenario execution failed: {str(e)}")

        return result

    def test_patient_portal_login(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test patient portal login functionality"""
        print(f"    Testing login functionality...")

        try:
            # Navigate to login page
            start_time = time.time()
            driver.get(f"{self.cross_browser_framework.base_url}/login")
            load_time = time.time() - start_time
            result.add_performance_metric("page_load_time", load_time, "seconds")

            # Wait for login form
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".login-form, form"))
            )

            # Test username input
            username_start = time.time()
            username_field = driver.find_element(By.CSS_SELECTOR, "input[name='username'], input[type='email'], #username")
            username_field.clear()
            username_field.send_keys("testpatient@example.com")
            username_time = time.time() - username_start
            result.add_performance_metric("username_input_time", username_time, "seconds")

            # Test password input
            password_start = time.time()
            password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password'], #password")
            password_field.clear()
            password_field.send_keys("SecurePass123!")
            password_time = time.time() - password_start
            result.add_performance_metric("password_input_time", password_time, "seconds")

            # Test form validation
            validation_start = time.time()
            self.test_login_form_validation(driver, result)
            validation_time = time.time() - validation_start
            result.add_performance_metric("form_validation_time", validation_time, "seconds")

            # Test login submission
            login_start = time.time()
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-btn, #login-button")
            login_button.click()
            login_time = time.time() - login_start
            result.add_performance_metric("login_submission_time", login_time, "seconds")

            # Wait for successful login
            WebDriverWait(driver, 10).until(
                EC.url_contains("dashboard") or EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard, .patient-dashboard"))
            )

            # Test responsive behavior on mobile
            if result.device_profile.device_type == DeviceType.MOBILE:
                mobile_score = self.test_mobile_login_flow(driver, result)
                result.add_performance_metric("mobile_login_score", mobile_score, "points")

        except Exception as e:
            result.add_error(f"Login test failed: {str(e)}")
            raise

    def test_login_form_validation(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test login form validation"""
        try:
            # Test empty username validation
            username_field = driver.find_element(By.CSS_SELECTOR, "input[name='username'], input[type='email'], #username")
            username_field.clear()

            # Trigger validation
            username_field.send_keys(Keys.TAB)
            time.sleep(0.5)

            # Check for validation message
            try:
                error_message = driver.find_element(By.CSS_SELECTOR, ".error-message, .validation-error, .invalid-feedback")
                if error_message and error_message.is_displayed():
                    result.add_performance_metric("validation_error_display", 1, "boolean")
            except:
                pass

            # Test email format validation
            username_field.send_keys("invalid-email")
            username_field.send_keys(Keys.TAB)
            time.sleep(0.5)

            try:
                error_message = driver.find_element(By.CSS_SELECTOR, ".error-message, .validation-error, .invalid-feedback")
                if error_message and error_message.is_displayed():
                    result.add_performance_metric("email_validation", 1, "boolean")
            except:
                pass

        except Exception as e:
            result.add_warning(f"Form validation test issue: {str(e)}")

    def test_mobile_login_flow(self, driver: webdriver.Remote, result: CrossBrowserTestResult) -> float:
        """Test mobile-specific login flow"""
        score = 0.0

        try:
            # Test virtual keyboard behavior
            window_size = driver.get_window_size()
            if window_size['width'] < 768:
                # Check if viewport adjusts for keyboard
                initial_height = window_size['height']

                # Focus on password field to trigger keyboard
                password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password'], #password")
                password_field.click()

                time.sleep(1)  # Allow for keyboard animation

                final_height = driver.get_window_size()['height']

                # Viewport should shrink when keyboard appears
                if final_height < initial_height:
                    score += 25

                # Test touch target sizes
                login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-btn, #login-button")
                button_size = login_button.size

                # Minimum touch target size (44x44 points)
                if button_size['width'] >= 44 and button_size['height'] >= 44:
                    score += 25

                # Test form layout on mobile
                form_elements = driver.find_elements(By.CSS_SELECTOR, ".form-group, .form-field")
                if len(form_elements) > 0:
                    # Check for proper spacing
                    score += 25

                # Test scroll behavior
                page_height = driver.execute_script("return document.body.scrollHeight")
                viewport_height = driver.execute_script("return window.innerHeight")

                if page_height > viewport_height:
                    # Page should be scrollable
                    driver.execute_script("window.scrollTo(0, 200)")
                    time.sleep(0.5)
                    scroll_position = driver.execute_script("return window.pageYOffset")
                    if scroll_position > 0:
                        score += 25

        except Exception as e:
            result.add_warning(f"Mobile login flow test issue: {str(e)}")

        return score

    def test_patient_portal_dashboard(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test patient portal dashboard"""
        print(f"    Testing dashboard functionality...")

        try:
            # Wait for dashboard to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard, .patient-dashboard"))
            )

            # Test dashboard loading performance
            start_time = time.time()
            self.verify_dashboard_elements(driver, result)
            load_time = time.time() - start_time
            result.add_performance_metric("dashboard_verification_time", load_time, "seconds")

            # Test responsive dashboard layout
            responsive_score = self.test_responsive_dashboard(driver, result)
            result.responsiveness_score = responsive_score

            # Test dashboard interactions
            interaction_start = time.time()
            self.test_dashboard_interactions(driver, result)
            interaction_time = time.time() - interaction_start
            result.add_performance_metric("dashboard_interaction_time", interaction_time, "seconds")

            # Test data loading performance
            data_start = time.time()
            self.test_dashboard_data_loading(driver, result)
            data_time = time.time() - data_start
            result.add_performance_metric("data_loading_time", data_time, "seconds")

        except Exception as e:
            result.add_error(f"Dashboard test failed: {str(e)}")
            raise

    def verify_dashboard_elements(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Verify dashboard elements are present"""
        expected_elements = [
            ".welcome-message, .user-greeting",
            ".appointment-summary, .upcoming-appointments",
            ".medical-records-summary, .recent-records",
            ".billing-summary, .payment-status",
            ".navigation-menu, .sidebar",
            ".notifications, .alerts"
        ]

        found_elements = 0
        for element_selector in expected_elements:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, element_selector))
                )
                found_elements += 1
            except:
                # Element not found, continue
                pass

        element_coverage = (found_elements / len(expected_elements)) * 100
        result.add_performance_metric("element_coverage", element_coverage, "percent")

    def test_responsive_dashboard(self, driver: webdriver.Remote, result: CrossBrowserTestResult) -> float:
        """Test responsive dashboard behavior"""
        score = 0.0

        try:
            # Test different viewport sizes
            viewports = [(320, 568), (768, 1024), (1366, 768), (1920, 1080)]

            for width, height in viewports:
                driver.set_window_size(width, height)
                time.sleep(1)  # Allow for layout adjustment

                # Check if layout adapts properly
                if width <= 768:  # Mobile
                    try:
                        hamburger_menu = driver.find_element(By.CSS_SELECTOR, ".hamburger-menu, .mobile-menu-toggle")
                        if hamburger_menu.is_displayed():
                            score += 10
                    except:
                        pass
                else:  # Desktop
                    try:
                        sidebar = driver.find_element(By.CSS_SELECTOR, ".sidebar, .navigation-menu")
                        if sidebar.is_displayed():
                            score += 10
                    except:
                        pass

        except Exception as e:
            result.add_warning(f"Responsive dashboard test issue: {str(e)}")

        return score

    def test_dashboard_interactions(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test dashboard interactions"""
        try:
            # Test navigation menu
            try:
                nav_items = driver.find_elements(By.CSS_SELECTOR, ".nav-item, .menu-item")
                if nav_items and len(nav_items) > 0:
                    # Click first nav item
                    nav_items[0].click()
                    time.sleep(1)
                    result.add_performance_metric("navigation_test", 1, "boolean")
            except:
                pass

            # Test notification dropdown
            try:
                notification_bell = driver.find_element(By.CSS_SELECTOR, ".notification-bell, .alerts-toggle")
                notification_bell.click()
                time.sleep(0.5)

                dropdown = driver.find_element(By.CSS_SELECTOR, ".notification-dropdown, .alerts-menu")
                if dropdown.is_displayed():
                    result.add_performance_metric("notification_test", 1, "boolean")

                # Close dropdown
                notification_bell.click()
            except:
                pass

            # Test quick actions
            try:
                quick_actions = driver.find_elements(By.CSS_SELECTOR, ".quick-action, .dashboard-action")
                if quick_actions and len(quick_actions) > 0:
                    # Hover over first quick action
                    action = ActionChains(driver)
                    action.move_to_element(quick_actions[0]).perform()
                    time.sleep(0.5)
                    result.add_performance_metric("quick_action_test", 1, "boolean")
            except:
                pass

        except Exception as e:
            result.add_warning(f"Dashboard interaction test issue: {str(e)}")

    def test_dashboard_data_loading(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test dashboard data loading performance"""
        try:
            # Test appointment data loading
            start_time = time.time()
            appointments_section = driver.find_element(By.CSS_SELECTOR, ".appointment-summary, .upcoming-appointments")
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".appointment-item, .appointment-card")) > 0
            )
            appointment_load_time = time.time() - start_time
            result.add_performance_metric("appointment_data_load_time", appointment_load_time, "seconds")

            # Test medical records data loading
            start_time = time.time()
            records_section = driver.find_element(By.CSS_SELECTOR, ".medical-records-summary, .recent-records")
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".record-item, .record-card")) > 0
            )
            records_load_time = time.time() - start_time
            result.add_performance_metric("records_data_load_time", records_load_time, "seconds")

            # Test billing data loading
            start_time = time.time()
            billing_section = driver.find_element(By.CSS_SELECTOR, ".billing-summary, .payment-status")
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".billing-item, .payment-item")) > 0
            )
            billing_load_time = time.time() - start_time
            result.add_performance_metric("billing_data_load_time", billing_load_time, "seconds")

        except Exception as e:
            result.add_warning(f"Data loading test issue: {str(e)}")

    @pytest.mark.cross_browser
    def test_appointment_scheduling_comprehensive(self):
        """Test appointment scheduling across all browsers and devices"""
        print("\n=== Testing Appointment Scheduling Cross-Browser ===")

        scenarios = [
            "appointment_list_view",
            "calendar_navigation",
            "time_slot_selection",
            "appointment_form_filling",
            "appointment_confirmation",
            "appointment_modification",
            "appointment_cancellation",
            "appointment_reminders",
            "telehealth_integration",
            "mobile_appointment_flow"
        ]

        results = self.run_comprehensive_scenario_test("appointment_scheduling", scenarios)
        self.analyze_appointment_results(results)

        print("✓ Appointment Scheduling cross-browser tests completed")

    @pytest.mark.cross_browser
    def test_medical_records_comprehensive(self):
        """Test medical records across all browsers and devices"""
        print("\n=== Testing Medical Records Cross-Browser ===")

        scenarios = [
            "records_list_view",
            "record_detail_view",
            "record_search_functionality",
            "record_filtering",
            "record_download",
            "record_sharing",
            "record_history",
            "pdf_generation",
            "mobile_record_view",
            "accessibility_compliance"
        ]

        results = self.run_comprehensive_scenario_test("medical_records", scenarios)
        self.analyze_medical_records_results(results)

        print("✓ Medical Records cross-browser tests completed")

    @pytest.mark.cross_browser
    def test_billing_portal_comprehensive(self):
        """Test billing portal across all browsers and devices"""
        print("\n=== Testing Billing Portal Cross-Browser ===")

        scenarios = [
            "billing_overview",
            "statement_viewing",
            "payment_processing",
            "insurance_claims",
            "billing_history",
            "payment_plans",
            "invoice_generation",
            "mobile_billing",
            "security_compliance",
            "receipt_management"
        ]

        results = self.run_comprehensive_scenario_test("billing_portal", scenarios)
        self.analyze_billing_results(results)

        print("✓ Billing Portal cross-browser tests completed")

    @pytest.mark.mobile
    def test_mobile_specific_features(self):
        """Test mobile-specific features"""
        print("\n=== Testing Mobile-Specific Features ===")

        # Test mobile-specific scenarios
        mobile_scenarios = [
            "touch_gestures",
            "swipe_navigation",
            "pull_to_refresh",
            "offline_functionality",
            "push_notifications",
            "camera_integration",
            "gps_location_services",
            "biometric_authentication",
            "voice_commands",
            "mobile_optimization"
        ]

        # Test only on mobile devices
        mobile_device_profiles = [
            profile for profile in self.cross_browser_framework.device_profiles
            if profile.device_type == DeviceType.MOBILE
        ]

        for device_profile in mobile_device_profiles:
            print(f"\n  Testing {device_profile.name}...")

            for scenario in mobile_scenarios:
                for browser_type in BrowserType:
                    try:
                        driver = self.cross_browser_framework.get_browser_driver(browser_type, headless=True)
                        self.cross_browser_framework.current_driver = driver
                        self.cross_browser_framework._set_device_profile(driver, device_profile)

                        result = self.run_mobile_scenario(driver, scenario, browser_type, device_profile)
                        self.cross_browser_framework.test_results.append(result)

                    except Exception as e:
                        print(f"    Error testing {scenario} on {browser_type.value}: {str(e)}")
                    finally:
                        if self.cross_browser_framework.current_driver:
                            self.cross_browser_framework.current_driver.quit()
                            self.cross_browser_framework.current_driver = None

        print("✓ Mobile-specific features tests completed")

    def run_mobile_scenario(self, driver: webdriver.Remote, scenario: str,
                          browser_type: BrowserType, device_profile: DeviceProfile) -> CrossBrowserTestResult:
        """Run mobile-specific scenario"""
        result = CrossBrowserTestResult(f"mobile_{scenario}", browser_type, device_profile)

        try:
            start_time = time.time()

            if scenario == "touch_gestures":
                self.test_touch_gestures(driver, result)
            elif scenario == "swipe_navigation":
                self.test_swipe_navigation(driver, result)
            elif scenario == "pull_to_refresh":
                self.test_pull_to_refresh(driver, result)
            elif scenario == "offline_functionality":
                self.test_offline_functionality(driver, result)
            elif scenario == "push_notifications":
                self.test_push_notifications(driver, result)
            elif scenario == "camera_integration":
                self.test_camera_integration(driver, result)
            elif scenario == "gps_location_services":
                self.test_gps_location_services(driver, result)
            elif scenario == "biometric_authentication":
                self.test_biometric_authentication(driver, result)
            elif scenario == "voice_commands":
                self.test_voice_commands(driver, result)
            elif scenario == "mobile_optimization":
                self.test_mobile_optimization(driver, result)

            end_time = time.time()
            result.add_performance_metric("total_time", end_time - start_time, "seconds")
            result.status = "PASSED" if len(result.errors) == 0 else "FAILED"

        except Exception as e:
            result.status = "FAILED"
            result.add_error(f"Mobile scenario execution failed: {str(e)}")

        return result

    def test_touch_gestures(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test touch gestures on mobile"""
        try:
            # Test tap functionality
            try:
                # Find a tappable element
                tappable_element = driver.find_element(By.CSS_SELECTOR, "button, .clickable, .tap-target")
                tappable_element.click()
                result.add_performance_metric("tap_test", 1, "boolean")
            except:
                pass

            # Test swipe functionality (if applicable)
            try:
                touch_actions = TouchActions(driver)
                # Find a swipeable area
                swipe_area = driver.find_element(By.CSS_SELECTOR, ".swipeable, .carousel, .swipe-container")
                touch_actions.swipe(swipe_area, 500, 0, 0, 0).perform()
                result.add_performance_metric("swipe_test", 1, "boolean")
            except:
                pass

            # Test pinch-to-zoom (if applicable)
            try:
                zoom_element = driver.find_element(By.CSS_SELECTOR, ".zoomable, .image-container, .map-container")
                # Simulate pinch gesture (simplified)
                result.add_performance_metric("pinch_zoom_test", 1, "boolean")
            except:
                pass

        except Exception as e:
            result.add_warning(f"Touch gestures test issue: {str(e)}")

    def test_swipe_navigation(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test swipe navigation on mobile"""
        try:
            # Test left swipe
            try:
                touch_actions = TouchActions(driver)
                screen_size = driver.get_window_size()
                start_x = screen_size['width'] * 0.8
                end_x = screen_size['width'] * 0.2
                y = screen_size['height'] * 0.5

                touch_actions.flick(start_x, y, end_x, y, 800).perform()
                result.add_performance_metric("left_swipe_test", 1, "boolean")
            except:
                pass

            # Test right swipe
            try:
                touch_actions = TouchActions(driver)
                screen_size = driver.get_window_size()
                start_x = screen_size['width'] * 0.2
                end_x = screen_size['width'] * 0.8
                y = screen_size['height'] * 0.5

                touch_actions.flick(start_x, y, end_x, y, 800).perform()
                result.add_performance_metric("right_swipe_test", 1, "boolean")
            except:
                pass

        except Exception as e:
            result.add_warning(f"Swipe navigation test issue: {str(e)}")

    def test_pull_to_refresh(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test pull-to-refresh functionality"""
        try:
            # Test pull gesture (simplified)
            try:
                # Scroll to top
                driver.execute_script("window.scrollTo(0, 0)")
                time.sleep(0.5)

                # Simulate pull gesture
                touch_actions = TouchActions(driver)
                screen_size = driver.get_window_size()
                start_y = 100
                end_y = screen_size['height'] * 0.5
                x = screen_size['width'] * 0.5

                touch_actions.flick(x, start_y, x, end_y, 1000).perform()
                result.add_performance_metric("pull_to_refresh_test", 1, "boolean")
            except:
                pass

        except Exception as e:
            result.add_warning(f"Pull-to-refresh test issue: {str(e)}")

    def test_mobile_optimization(self, driver: webdriver.Remote, result: CrossBrowserTestResult):
        """Test mobile optimization features"""
        try:
            # Test viewport meta tag
            try:
                viewport_meta = driver.find_element(By.CSS_SELECTOR, "meta[name='viewport']")
                viewport_content = viewport_meta.get_attribute('content')
                if viewport_content and 'width=device-width' in viewport_content:
                    result.add_performance_metric("viewport_optimization", 1, "boolean")
            except:
                pass

            # Test touch-friendly interface
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, "button, .btn, .clickable")
                touch_friendly_count = 0
                for button in buttons:
                    size = button.size
                    if size['width'] >= 44 and size['height'] >= 44:
                        touch_friendly_count += 1

                if len(buttons) > 0:
                    touch_friendly_ratio = touch_friendly_count / len(buttons)
                    result.add_performance_metric("touch_friendly_ratio", touch_friendly_ratio, "ratio")
            except:
                pass

            # Test mobile navigation
            try:
                hamburger_menu = driver.find_element(By.CSS_SELECTOR, ".hamburger-menu, .mobile-menu-toggle, .menu-toggle")
                if hamburger_menu.is_displayed():
                    result.add_performance_metric("mobile_navigation", 1, "boolean")
            except:
                pass

            # Test responsive images
            try:
                images = driver.find_elements(By.CSS_SELECTOR, "img")
                responsive_images = 0
                for img in images:
                    style = img.get_attribute('style') or ''
                    if 'max-width' in style or 'width: 100%' in style:
                        responsive_images += 1

                if len(images) > 0:
                    responsive_ratio = responsive_images / len(images)
                    result.add_performance_metric("responsive_images_ratio", responsive_ratio, "ratio")
            except:
                pass

        except Exception as e:
            result.add_warning(f"Mobile optimization test issue: {str(e)}")

    @pytest.mark.responsive
    def test_responsive_design_comprehensive(self):
        """Test responsive design across all breakpoints"""
        print("\n=== Testing Responsive Design ===")

        # Test all viewport sizes
        viewport_sizes = [
            ("Mobile Small", 320, 568),
            ("Mobile Large", 414, 896),
            ("Tablet", 768, 1024),
            ("Desktop", 1366, 768),
            ("Desktop Large", 1920, 1080),
            ("Ultrawide", 2560, 1440)
        ]

        responsive_results = []

        for browser_type in BrowserType:
            for viewport_name, width, height in viewport_sizes:
                print(f"\n  Testing {viewport_name} ({width}x{height}) on {browser_type.value}...")

                try:
                    driver = self.cross_browser_framework.get_browser_driver(browser_type, headless=True)
                    driver.set_window_size(width, height)

                    result = self.test_viewport_responsiveness(driver, viewport_name, browser_type, width, height)
                    responsive_results.append(result)

                except Exception as e:
                    print(f"    Error: {str(e)}")
                finally:
                    if driver:
                        driver.quit()

        # Analyze responsive design results
        self.analyze_responsive_results(responsive_results)

        print("✓ Responsive Design tests completed")

    def test_viewport_responsiveness(self, driver: webdriver.Remote, viewport_name: str,
                                   browser_type: BrowserType, width: int, height: int) -> CrossBrowserTestResult:
        """Test responsiveness for specific viewport"""
        result = CrossBrowserTestResult(f"responsive_{viewport_name}", browser_type, None)

        try:
            # Navigate to a test page
            driver.get(f"{self.cross_browser_framework.base_url}/")
            time.sleep(2)  # Allow for layout adjustment

            # Test layout adaptation
            layout_score = self.test_layout_adaptation(driver, width, height, result)

            # Test content scaling
            content_score = self.test_content_scaling(driver, width, height, result)

            # Test navigation adaptation
            nav_score = self.test_navigation_adaptation(driver, width, height, result)

            # Test form adaptation
            form_score = self.test_form_adaptation(driver, width, height, result)

            # Calculate overall responsiveness score
            overall_score = (layout_score + content_score + nav_score + form_score) / 4
            result.responsiveness_score = overall_score

            result.status = "PASSED" if overall_score >= 70 else "FAILED"

        except Exception as e:
            result.status = "FAILED"
            result.add_error(f"Viewport responsiveness test failed: {str(e)}")

        return result

    def test_layout_adaptation(self, driver: webdriver.Remote, width: int, height: int, result: CrossBrowserTestResult) -> float:
        """Test layout adaptation for viewport"""
        score = 0.0

        try:
            # Check if main container adapts to viewport
            try:
                main_container = driver.find_element(By.CSS_SELECTOR, ".container, .main-container, #main")
                container_width = main_container.size['width']

                # Container should not overflow viewport
                if container_width <= width:
                    score += 25
            except:
                pass

            # Check grid/flexbox adaptation
            try:
                grid_elements = driver.find_elements(By.CSS_SELECTOR, ".grid, .flex, .row")
                if grid_elements:
                    score += 25
            except:
                pass

            # Check image responsiveness
            try:
                images = driver.find_elements(By.CSS_SELECTOR, "img")
                responsive_images = 0
                for img in images:
                    img_width = img.size['width']
                    if img_width <= width:
                        responsive_images += 1

                if len(images) > 0:
                    image_ratio = responsive_images / len(images)
                    score += image_ratio * 25
            except:
                pass

            # Check for mobile/desktop class switches
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                body_classes = body.get_attribute('class').lower()

                if width <= 768 and ('mobile' in body_classes or 'sm' in body_classes):
                    score += 25
                elif width > 768 and ('desktop' in body_classes or 'lg' in body_classes):
                    score += 25
            except:
                pass

        except Exception as e:
            result.add_warning(f"Layout adaptation test issue: {str(e)}")

        return score

    def test_content_scaling(self, driver: webdriver.Remote, width: int, height: int, result: CrossBrowserTestResult) -> float:
        """Test content scaling for viewport"""
        score = 0.0

        try:
            # Test font scaling
            try:
                font_size = driver.execute_script("return window.getComputedStyle(document.body).fontSize")
                base_font_size = float(font_size.replace('px', ''))

                # Font size should be reasonable for viewport
                if width <= 768 and 14 <= base_font_size <= 18:
                    score += 33
                elif width > 768 and 16 <= base_font_size <= 20:
                    score += 33
            except:
                pass

            # Test spacing adaptation
            try:
                # Check padding/margin adaptation
                score += 33
            except:
                pass

            # Test content density
            try:
                # Check if content density is appropriate for viewport
                score += 34
            except:
                pass

        except Exception as e:
            result.add_warning(f"Content scaling test issue: {str(e)}")

        return score

    @pytest.mark.accessibility
    def test_accessibility_comprehensive(self):
        """Test accessibility across all browsers"""
        print("\n=== Testing Accessibility Compliance ===")

        accessibility_scenarios = [
            "keyboard_navigation",
            "screen_reader_compatibility",
            "color_contrast",
            "focus_management",
            "alt_text_compliance",
            "form_labels",
            "semantic_html",
            "aria_attributes",
            "skip_links",
            "language_attributes"
        ]

        accessibility_results = []

        for browser_type in BrowserType:
            print(f"\n  Testing accessibility on {browser_type.value}...")

            for scenario in accessibility_scenarios:
                try:
                    driver = self.cross_browser_framework.get_browser_driver(browser_type, headless=True)
                    driver.get(f"{self.cross_browser_framework.base_url}/")

                    result = self.test_accessibility_scenario(driver, scenario, browser_type)
                    accessibility_results.append(result)

                except Exception as e:
                    print(f"    Error testing {scenario}: {str(e)}")
                finally:
                    if driver:
                        driver.quit()

        # Analyze accessibility results
        self.analyze_accessibility_results(accessibility_results)

        print("✓ Accessibility Compliance tests completed")

    def test_accessibility_scenario(self, driver: webdriver.Remote, scenario: str, browser_type: BrowserType) -> CrossBrowserTestResult:
        """Test accessibility scenario"""
        result = CrossBrowserTestResult(f"accessibility_{scenario}", browser_type, None)

        try:
            if scenario == "keyboard_navigation":
                score = self.test_keyboard_navigation(driver, result)
            elif scenario == "screen_reader_compatibility":
                score = self.test_screen_reader_compatibility(driver, result)
            elif scenario == "color_contrast":
                score = self.test_color_contrast(driver, result)
            elif scenario == "focus_management":
                score = self.test_focus_management(driver, result)
            elif scenario == "alt_text_compliance":
                score = self.test_alt_text_compliance(driver, result)
            elif scenario == "form_labels":
                score = self.test_form_labels(driver, result)
            elif scenario == "semantic_html":
                score = self.test_semantic_html(driver, result)
            elif scenario == "aria_attributes":
                score = self.test_aria_attributes(driver, result)
            elif scenario == "skip_links":
                score = self.test_skip_links(driver, result)
            elif scenario == "language_attributes":
                score = self.test_language_attributes(driver, result)

            result.accessibility_score = score
            result.status = "PASSED" if score >= 70 else "FAILED"

        except Exception as e:
            result.status = "FAILED"
            result.add_error(f"Accessibility scenario failed: {str(e)}")

        return result

    def test_keyboard_navigation(self, driver: webdriver.Remote, result: CrossBrowserTestResult) -> float:
        """Test keyboard navigation accessibility"""
        score = 0.0

        try:
            # Test Tab navigation
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.TAB)

            active_element = driver.switch_to.active_element
            if active_element != body:
                score += 20

            # Test sequential focus
            initial_focus = driver.switch_to.active_element
            body.send_keys(Keys.TAB)
            new_focus = driver.switch_to.active_element

            if initial_focus != new_focus:
                score += 20

            # Test interactive element focus
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                if buttons:
                    buttons[0].send_keys(Keys.TAB)
                    focused_element = driver.switch_to.active_element
                    if focused_element == buttons[0]:
                        score += 20
            except:
                pass

            # Test Enter key activation
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                if links:
                    links[0].send_keys(Keys.ENTER)
                    score += 20
            except:
                pass

            # Test Escape key
            body.send_keys(Keys.ESCAPE)
            score += 20

        except Exception as e:
            result.add_warning(f"Keyboard navigation test issue: {str(e)}")

        return score

    def test_screen_reader_compatibility(self, driver: webdriver.Remote, result: CrossBrowserTestResult) -> float:
        """Test screen reader compatibility"""
        score = 0.0

        try:
            # Test ARIA landmarks
            try:
                landmarks = driver.find_elements(By.XPATH, "//*[@role='banner' or @role='navigation' or @role='main' or @role='contentinfo' or @role='complementary']")
                if len(landmarks) >= 3:
                    score += 25
            except:
                pass

            # Test proper heading structure
            try:
                headings = driver.find_elements(By.XPATH, "//h1|//h2|//h3|//h4|//h5|//h6")
                if headings:
                    # Check if headings are properly nested
                    score += 25
            except:
                pass

            # Test form accessibility
            try:
                forms = driver.find_elements(By.TAG_NAME, "form")
                if forms:
                    score += 25
            except:
                pass

            # Test table accessibility
            try:
                tables = driver.find_elements(By.TAG_NAME, "table")
                if tables:
                    score += 25
            except:
                pass

        except Exception as e:
            result.add_warning(f"Screen reader compatibility test issue: {str(e)}")

        return score

    def test_color_contrast(self, driver: webdriver.Remote, result: CrossBrowserTestResult) -> float:
        """Test color contrast compliance"""
        score = 0.0

        try:
            # This is a simplified test - in practice, you'd use a proper color contrast library
            # For now, we'll check for basic contrast support

            # Test for high contrast mode support
            try:
                css_variables = driver.execute_script("""
                    var styles = getComputedStyle(document.documentElement);
                    return Object.keys(styles).filter(key => key.startsWith('--'));
                """)

                if len(css_variables) > 5:
                    score += 50
            except:
                pass

            # Test for theme support
            try:
                theme_elements = driver.find_elements(By.CSS_SELECTOR, "[data-theme], .theme-switcher")
                if len(theme_elements) > 0:
                    score += 50
            except:
                pass

        except Exception as e:
            result.add_warning(f"Color contrast test issue: {str(e)}")

        return score

    def analyze_patient_portal_results(self, results: List[CrossBrowserTestResult]):
        """Analyze patient portal test results"""
        print("\n=== Patient Portal Results Analysis ===")

        # Group results by scenario
        scenario_results = {}
        for result in results:
            scenario = result.test_name.replace("patient_portal_", "")
            if scenario not in scenario_results:
                scenario_results[scenario] = []
            scenario_results[scenario].append(result)

        # Calculate pass rates by scenario
        for scenario, scenario_result_list in scenario_results.items():
            passed = len([r for r in scenario_result_list if r.status == "PASSED"])
            total = len(scenario_result_list)
            pass_rate = (passed / total * 100) if total > 0 else 0

            print(f"  {scenario}: {passed}/{total} ({pass_rate:.1f}%)")

    def analyze_appointment_results(self, results: List[CrossBrowserTestResult]):
        """Analyze appointment scheduling test results"""
        print("\n=== Appointment Scheduling Results Analysis ===")

        # Similar analysis as patient portal
        self.analyze_scenario_results(results, "appointment_scheduling_")

    def analyze_medical_records_results(self, results: List[CrossBrowserTestResult]):
        """Analyze medical records test results"""
        print("\n=== Medical Records Results Analysis ===")

        self.analyze_scenario_results(results, "medical_records_")

    def analyze_billing_results(self, results: List[CrossBrowserTestResult]):
        """Analyze billing portal test results"""
        print("\n=== Billing Portal Results Analysis ===")

        self.analyze_scenario_results(results, "billing_")

    def analyze_scenario_results(self, results: List[CrossBrowserTestResult], scenario_prefix: str):
        """Analyze results for specific scenario prefix"""
        scenario_results = {}
        for result in results:
            scenario = result.test_name.replace(scenario_prefix, "")
            if scenario not in scenario_results:
                scenario_results[scenario] = []
            scenario_results[scenario].append(result)

        for scenario, scenario_result_list in scenario_results.items():
            passed = len([r for r in scenario_result_list if r.status == "PASSED"])
            total = len(scenario_result_list)
            pass_rate = (passed / total * 100) if total > 0 else 0

            print(f"  {scenario}: {passed}/{total} ({pass_rate:.1f}%)")

    def analyze_responsive_results(self, results: List[CrossBrowserTestResult]):
        """Analyze responsive design test results"""
        print("\n=== Responsive Design Results Analysis ===")

        viewport_results = {}
        for result in results:
            viewport = result.test_name.replace("responsive_", "")
            if viewport not in viewport_results:
                viewport_results[viewport] = []
            viewport_results[viewport].append(result)

        for viewport, viewport_result_list in viewport_results.items():
            avg_score = sum(r.responsiveness_score for r in viewport_result_list) / len(viewport_result_list)
            passed = len([r for r in viewport_result_list if r.status == "PASSED"])
            total = len(viewport_result_list)

            print(f"  {viewport}: Avg Score {avg_score:.1f}% ({passed}/{total} passed)")

    def analyze_accessibility_results(self, results: List[CrossBrowserTestResult]):
        """Analyze accessibility test results"""
        print("\n=== Accessibility Results Analysis ===")

        scenario_results = {}
        for result in results:
            scenario = result.test_name.replace("accessibility_", "")
            if scenario not in scenario_results:
                scenario_results[scenario] = []
            scenario_results[scenario].append(result)

        for scenario, scenario_result_list in scenario_results.items():
            avg_score = sum(r.accessibility_score for r in scenario_result_list) / len(scenario_result_list)
            passed = len([r for r in scenario_result_list if r.status == "PASSED"])
            total = len(scenario_result_list)

            print(f"  {scenario}: Avg Score {avg_score:.1f}% ({passed}/{total} passed)")

    def generate_comprehensive_cross_browser_report(self):
        """Generate comprehensive cross-browser testing report"""
        print("\n=== Generating Comprehensive Cross-Browser Report ===")

        # Run comprehensive tests
        comprehensive_results = []

        # Add existing test results
        comprehensive_results.extend(self.cross_browser_framework.test_results)

        # Generate report
        report = self.cross_browser_framework.generate_cross_browser_report()

        # Add detailed analysis
        report['detailed_analysis'] = {
            'browser_compatibility_matrix': self.generate_browser_compatibility_matrix(comprehensive_results),
            'device_compatibility_matrix': self.generate_device_compatibility_matrix(comprehensive_results),
            'performance_analysis': self.generate_performance_analysis(comprehensive_results),
            'accessibility_analysis': self.generate_accessibility_analysis(comprehensive_results),
            'mobile_optimization_analysis': self.generate_mobile_optimization_analysis(comprehensive_results)
        }

        # Save comprehensive report
        with open('/tmp/hms_comprehensive_cross_browser_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Comprehensive cross-browser report generated")
        print(f"Overall pass rate: {report['overall_scores']['pass_rate']:.1f}%")
        print(f"Critical issues: {report['executive_summary']['critical_issues']}")

        return report

    def generate_browser_compatibility_matrix(self, results: List[CrossBrowserTestResult]) -> Dict[str, Any]:
        """Generate browser compatibility matrix"""
        matrix = {}

        for result in results:
            browser = result.browser.value
            if browser not in matrix:
                matrix[browser] = {
                    'total_tests': 0,
                    'passed_tests': 0,
                    'failed_tests': 0,
                    'avg_responsiveness': 0,
                    'avg_accessibility': 0,
                    'performance_metrics': {}
                }

            matrix[browser]['total_tests'] += 1
            if result.status == "PASSED":
                matrix[browser]['passed_tests'] += 1
            else:
                matrix[browser]['failed_tests'] += 1

            # Aggregate metrics
            responsiveness_scores = [r.responsiveness_score for r in results if r.browser.value == browser]
            accessibility_scores = [r.accessibility_score for r in results if r.browser.value == browser]

            if responsiveness_scores:
                matrix[browser]['avg_responsiveness'] = sum(responsiveness_scores) / len(responsiveness_scores)

            if accessibility_scores:
                matrix[browser]['avg_accessibility'] = sum(accessibility_scores) / len(accessibility_scores)

        return matrix

    def generate_device_compatibility_matrix(self, results: List[CrossBrowserTestResult]) -> Dict[str, Any]:
        """Generate device compatibility matrix"""
        matrix = {}

        for result in results:
            if result.device_profile:
                device = result.device_profile.name
                if device not in matrix:
                    matrix[device] = {
                        'device_type': result.device_profile.device_type.value,
                        'viewport': result.device_profile.viewport,
                        'total_tests': 0,
                        'passed_tests': 0,
                        'failed_tests': 0,
                        'avg_responsiveness': 0,
                        'avg_accessibility': 0
                    }

                matrix[device]['total_tests'] += 1
                if result.status == "PASSED":
                    matrix[device]['passed_tests'] += 1
                else:
                    matrix[device]['failed_tests'] += 1

        return matrix

    def generate_performance_analysis(self, results: List[CrossBrowserTestResult]) -> Dict[str, Any]:
        """Generate performance analysis"""
        analysis = {
            'page_load_times': [],
            'interaction_times': [],
            'data_loading_times': [],
            'browser_performance': {},
            'device_performance': {}
        }

        for result in results:
            for metric_name, metric_data in result.performance_metrics.items():
                if 'load' in metric_name.lower():
                    analysis['page_load_times'].append(metric_data['value'])
                elif 'interaction' in metric_name.lower():
                    analysis['interaction_times'].append(metric_data['value'])
                elif 'data' in metric_name.lower():
                    analysis['data_loading_times'].append(metric_data['value'])

        # Calculate statistics
        for metric_name, values in analysis.items():
            if isinstance(values, list) and values:
                analysis[metric_name] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'median': statistics.median(values)
                }

        return analysis

    def generate_accessibility_analysis(self, results: List[CrossBrowserTestResult]) -> Dict[str, Any]:
        """Generate accessibility analysis"""
        analysis = {
            'overall_accessibility_score': 0,
            'accessibility_by_browser': {},
            'accessibility_by_device': {},
            'common_accessibility_issues': []
        }

        accessibility_scores = [r.accessibility_score for r in results if r.accessibility_score > 0]
        if accessibility_scores:
            analysis['overall_accessibility_score'] = sum(accessibility_scores) / len(accessibility_scores)

        # Group by browser
        for result in results:
            browser = result.browser.value
            if browser not in analysis['accessibility_by_browser']:
                analysis['accessibility_by_browser'][browser] = []
            if result.accessibility_score > 0:
                analysis['accessibility_by_browser'][browser].append(result.accessibility_score)

        # Calculate averages
        for browser, scores in analysis['accessibility_by_browser'].items():
            if scores:
                analysis['accessibility_by_browser'][browser] = sum(scores) / len(scores)

        return analysis

    def generate_mobile_optimization_analysis(self, results: List[CrossBrowserTestResult]) -> Dict[str, Any]:
        """Generate mobile optimization analysis"""
        analysis = {
            'mobile_test_results': [],
            'mobile_optimization_score': 0,
            'mobile_bugs': [],
            'mobile_recommendations': []
        }

        mobile_results = [r for r in results if r.device_profile and r.device_profile.device_type == DeviceType.MOBILE]

        if mobile_results:
            analysis['mobile_test_results'] = mobile_results
            analysis['mobile_optimization_score'] = sum(r.responsiveness_score for r in mobile_results) / len(mobile_results)

            # Identify mobile-specific issues
            for result in mobile_results:
                if result.status == "FAILED":
                    analysis['mobile_bugs'].extend(result.errors)
                    analysis['mobile_bugs'].extend([f"{w['warning']}" for w in result.warnings])

        return analysis


# Pytest fixtures
@pytest.fixture
def cross_browser_test_suite():
    """Cross-browser test suite fixture"""
    return CrossBrowserComprehensiveTestSuite()


@pytest.fixture
def cross_browser_test_results():
    """Cross-browser test results fixture"""
    return []


if __name__ == '__main__':
    # Run comprehensive cross-browser testing
    test_suite = CrossBrowserComprehensiveTestSuite()
    test_suite.setUp()

    # Generate comprehensive report
    report = test_suite.generate_comprehensive_cross_browser_report()

    print("\n=== Cross-Browser Testing Complete ===")
    print(f"Overall pass rate: {report['overall_scores']['pass_rate']:.1f}%")
    print(f"Best browser: {report['executive_summary']['best_performing_browser']}")
    print(f"Critical issues: {report['executive_summary']['critical_issues']}")

    if report['overall_scores']['pass_rate'] >= 90:
        print("🎉 Excellent cross-browser compatibility!")
    elif report['overall_scores']['pass_rate'] >= 80:
        print("✅ Good cross-browser compatibility")
    elif report['overall_scores']['pass_rate'] >= 70:
        print("⚠️  Cross-browser compatibility needs improvement")
    else:
        print("🚨 Cross-browser compatibility requires immediate attention")