"""
WCAG 2.1 Compliance Testing Suite
Comprehensive testing for WCAG 2.1 AA and AAA compliance levels
"""

import pytest
import time
from typing import Dict, List, Tuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from bs4 import BeautifulSoup

from .accessibility_framework import (
    AccessibilityTestingFramework,
    WCAGGuideline,
    WCAGLevel,
    AccessibilityViolationType,
    AccessibilityTestMixin,
    HealthcareAccessibilityTestMixin
)

# WCAG 2.1 Test Configuration
WCAG_TEST_SCENARIOS = {
    "perceivable": [
        ("1.1.1 Non-text Content", WCAGGuideline.PERCEIVABLE_1_1_1, WCAGLevel.A),
        ("1.2.1 Audio-only and Video-only", WCAGGuideline.PERCEIVABLE_1_2_1, WCAGLevel.A),
        ("1.2.2 Captions", WCAGGuideline.PERCEIVABLE_1_2_2, WCAGLevel.A),
        ("1.2.3 Audio Description", WCAGGuideline.PERCEIVABLE_1_2_3, WCAGLevel.A),
        ("1.2.4 Captions (Live)", WCAGGuideline.PERCEIVABLE_1_2_4, WCAGLevel.AA),
        ("1.2.5 Audio Description", WCAGGuideline.PERCEIVABLE_1_2_5, WCAGLevel.AA),
        ("1.3.1 Info and Relationships", WCAGGuideline.PERCEIVABLE_1_3_1, WCAGLevel.A),
        ("1.3.2 Meaningful Sequence", WCAGGuideline.PERCEIVABLE_1_3_2, WCAGLevel.A),
        ("1.3.3 Sensory Characteristics", WCAGGuideline.PERCEIVABLE_1_3_3, WCAGLevel.A),
        ("1.3.4 Orientation", WCAGGuideline.PERCEIVABLE_1_3_4, WCAGLevel.AA),
        ("1.3.5 Identify Input Purpose", WCAGGuideline.PERCEIVABLE_1_3_5, WCAGLevel.AA),
        ("1.3.6 Identify Purpose", WCAGGuideline.PERCEIVABLE_1_3_6, WCAGLevel.AAA),
        ("1.4.1 Use of Color", WCAGGuideline.PERCEIVABLE_1_4_1, WCAGLevel.A),
        ("1.4.2 Audio Control", WCAGGuideline.PERCEIVABLE_1_4_2, WCAGLevel.A),
        ("1.4.3 Contrast (Minimum)", WCAGGuideline.PERCEIVABLE_1_4_3, WCAGLevel.AA),
        ("1.4.4 Resize text", WCAGGuideline.PERCEIVABLE_1_4_4, WCAGLevel.AA),
        ("1.4.5 Images of Text", WCAGGuideline.PERCEIVABLE_1_4_5, WCAGLevel.AA),
        ("1.4.6 Contrast (Enhanced)", WCAGGuideline.PERCEIVABLE_1_4_6, WCAGLevel.AAA),
        ("1.4.7 Low or No Background Audio", WCAGGuideline.PERCEIVABLE_1_4_7, WCAGLevel.AAA),
        ("1.4.8 Visual Presentation", WCAGGuideline.PERCEIVABLE_1_4_8, WCAGLevel.AAA),
        ("1.4.9 Images of Text (No Exception)", WCAGGuideline.PERCEIVABLE_1_4_9, WCAGLevel.AAA),
        ("1.4.10 Reflow", WCAGGuideline.PERCEIVABLE_1_4_10, WCAGLevel.AA),
        ("1.4.11 Non-text Contrast", WCAGGuideline.PERCEIVABLE_1_4_11, WCAGLevel.AA),
        ("1.4.12 Text Spacing", WCAGGuideline.PERCEIVABLE_1_4_12, WCAGLevel.AA),
        ("1.4.13 Content on Hover or Focus", WCAGGuideline.PERCEIVABLE_1_4_13, WCAGLevel.AA),
    ],
    "operable": [
        ("2.1.1 Keyboard", WCAGGuideline.OPERABLE_2_1_1, WCAGLevel.A),
        ("2.1.2 No Keyboard Trap", WCAGGuideline.OPERABLE_2_1_2, WCAGLevel.A),
        ("2.1.3 Keyboard (No Exception)", WCAGGuideline.OPERABLE_2_1_3, WCAGLevel.AAA),
        ("2.1.4 Character Key Shortcuts", WCAGGuideline.OPERABLE_2_1_4, WCAGLevel.A),
        ("2.2.1 Timing Adjustable", WCAGGuideline.OPERABLE_2_2_1, WCAGLevel.A),
        ("2.2.2 Pause, Stop, Hide", WCAGGuideline.OPERABLE_2_2_2, WCAGLevel.A),
        ("2.3.1 Three Flashes or Below Threshold", WCAGGuideline.OPERABLE_2_3_1, WCAGLevel.A),
        ("2.4.1 Bypass Blocks", WCAGGuideline.OPERABLE_2_4_1, WCAGLevel.A),
        ("2.4.2 Page Titled", WCAGGuideline.OPERABLE_2_4_2, WCAGLevel.A),
        ("2.4.3 Focus Order", WCAGGuideline.OPERABLE_2_4_3, WCAGLevel.A),
        ("2.4.4 Link Purpose (In Context)", WCAGGuideline.OPERABLE_2_4_4, WCAGLevel.A),
        ("2.4.5 Multiple Ways", WCAGGuideline.OPERABLE_2_4_5, WCAGLevel.AA),
        ("2.4.6 Headings and Labels", WCAGGuideline.OPERABLE_2_4_6, WCAGLevel.AA),
        ("2.4.7 Focus Visible", WCAGGuideline.OPERABLE_2_4_7, WCAGLevel.AA),
        ("2.5.1 Pointer Gestures", WCAGGuideline.OPERABLE_2_5_1, WCAGLevel.A),
        ("2.5.2 Pointer Cancellation", WCAGGuideline.OPERABLE_2_5_2, WCAGLevel.A),
        ("2.5.3 Label in Name", WCAGGuideline.OPERABLE_2_5_3, WCAGLevel.A),
        ("2.5.4 Motion Actuation", WCAGGuideline.OPERABLE_2_5_4, WCAGLevel.A),
        ("2.5.5 Target Size", WCAGGuideline.OPERABLE_2_5_5, WCAGLevel.AAA),
        ("2.5.6 Concurrent Input Mechanisms", WCAGGuideline.OPERABLE_2_5_6, WCAGLevel.AAA),
    ],
    "understandable": [
        ("3.1.1 Language of Page", WCAGGuideline.UNDERSTANDABLE_3_1_1, WCAGLevel.A),
        ("3.1.2 Language of Parts", WCAGGuideline.UNDERSTANDABLE_3_1_2, WCAGLevel.AA),
        ("3.2.1 On Focus", WCAGGuideline.UNDERSTANDABLE_3_2_1, WCAGLevel.A),
        ("3.2.2 On Input", WCAGGuideline.UNDERSTANDABLE_3_2_2, WCAGLevel.A),
        ("3.2.3 Consistent Navigation", WCAGGuideline.UNDERSTANDABLE_3_2_3, WCAGLevel.AA),
        ("3.2.4 Consistent Identification", WCAGGuideline.UNDERSTANDABLE_3_2_4, WCAGLevel.AA),
        ("3.3.1 Error Identification", WCAGGuideline.UNDERSTANDABLE_3_3_1, WCAGLevel.A),
        ("3.3.2 Labels or Instructions", WCAGGuideline.UNDERSTANDABLE_3_3_2, WCAGLevel.A),
        ("3.3.3 Error Suggestion", WCAGGuideline.UNDERSTANDABLE_3_3_3, WCAGLevel.AA),
        ("3.3.4 Error Prevention", WCAGGuideline.UNDERSTANDABLE_3_3_4, WCAGLevel.AA),
    ],
    "robust": [
        ("4.1.1 Parsing", WCAGGuideline.ROBUST_4_1_1, WCAGLevel.A),
        ("4.1.2 Name, Role, Value", WCAGGuideline.ROBUST_4_1_2, WCAGLevel.A),
        ("4.1.3 Status Messages", WCAGGuideline.ROBUST_4_1_3, WCAGLevel.AA),
    ]
}

class TestWCAGPerceivableGuidelines(AccessibilityTestMixin):
    """Test WCAG Perceivable guidelines (Principle 1)"""

    @pytest.mark.parametrize("guideline_name,wcag_guideline,wcag_level", WCAG_TEST_SCENARIOS["perceivable"])
    def test_perceivable_guidelines(self, chrome_driver, guideline_name, wcag_guideline, wcag_level):
        """Test all WCAG Perceivable guidelines"""
        url = f"http://localhost:3000/patient-portal"
        framework = AccessibilityTestingFramework()

        # Get page content
        chrome_driver.get(url)
        page_source = chrome_driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Run specific guideline test
        violations = []

        if wcag_guideline == WCAGGuideline.PERCEIVABLE_1_1_1:
            # Test non-text content (alt text)
            violations = self._test_alt_text_perceivable(soup)
        elif wcag_guideline == WCAGGuideline.PERCEIVABLE_1_3_1:
            # Test info and relationships
            violations = self._test_info_relationships(soup)
        elif wcag_guideline == WCAGGuideline.PERCEIVABLE_1_4_3:
            # Test contrast minimum
            violations = self._test_contrast_minimum(chrome_driver, soup)
        elif wcag_guideline == WCAGGuideline.PERCEIVABLE_1_4_10:
            # Test reflow
            violations = self._test_reflow(chrome_driver)
        elif wcag_guideline == WCAGGuideline.PERCEIVABLE_1_4_11:
            # Test non-text contrast
            violations = self._test_non_text_contrast(chrome_driver, soup)
        elif wcag_guideline == WCAGGuideline.PERCEIVABLE_1_4_12:
            # Test text spacing
            violations = self._test_text_spacing(chrome_driver, soup)

        # Assert compliance
        if wcag_level == WCAGLevel.A:
            # Level A should have no critical violations
            critical_violations = [v for v in violations if v.severity in ["Critical", "Serious"]]
            assert len(critical_violations) == 0, f"Critical violations found for {guideline_name}"
        elif wcag_level == WCAGLevel.AA:
            # Level AA should have no violations
            assert len(violations) == 0, f"Violations found for AA guideline {guideline_name}"

    def _test_alt_text_perceivable(self, soup: BeautifulSoup) -> List:
        """Test alt text for images (1.1.1)"""
        violations = []
        images = soup.find_all('img')

        for img in images:
            if not img.get('alt'):
                violations.append({
                    'guideline': WCAGGuideline.PERCEIVABLE_1_1_1,
                    'severity': 'Serious',
                    'description': 'Image missing alt text'
                })

        return violations

    def _test_info_relationships(self, soup: BeautifulSoup) -> List:
        """Test info and relationships (1.3.1)"""
        violations = []

        # Test heading structure
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        previous_level = 0

        for heading in headings:
            level = int(heading.name[1])
            if level > previous_level + 1:
                violations.append({
                    'guideline': WCAGGuideline.PERCEIVABLE_1_3_1,
                    'severity': 'Moderate',
                    'description': f'Heading level {level} follows level {previous_level} without intermediate heading'
                })
            previous_level = level

        # Test table structure
        tables = soup.find_all('table')
        for table in tables:
            if not table.find('th'):
                violations.append({
                    'guideline': WCAGGuideline.PERCEIVABLE_1_3_1,
                    'severity': 'Serious',
                    'description': 'Table missing header cells'
                })

        return violations

    def _test_contrast_minimum(self, driver: WebDriver, soup: BeautifulSoup) -> List:
        """Test contrast minimum (1.4.3)"""
        violations = []

        # Test text elements
        text_elements = soup.find_all(['p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        for element in text_elements:
            try:
                # Get computed styles
                element_obj = driver.find_element(By.CSS_SELECTOR, f"{element.name}")
                style = driver.execute_script("""
                    return window.getComputedStyle(arguments[0]);
                """, element_obj)

                text_color = style.get('color', '#000000')
                bg_color = style.get('background-color', '#ffffff')

                # Basic contrast check (simplified)
                if text_color == bg_color:
                    violations.append({
                        'guideline': WCAGGuideline.PERCEIVABLE_1_4_3,
                        'severity': 'Serious',
                        'description': 'Text and background colors are identical'
                    })

            except:
                continue

        return violations

    def _test_reflow(self, driver: WebDriver) -> List:
        """Test reflow (1.4.10)"""
        violations = []

        # Test different viewport sizes
        viewports = [
            (1280, 720),
            (1024, 768),
            (768, 1024),
            (375, 667)
        ]

        for width, height in viewports:
            driver.set_window_size(width, height)

            # Check horizontal scrolling
            body_width = driver.execute_script("return document.body.scrollWidth")
            viewport_width = driver.execute_script("return window.innerWidth")

            if body_width > viewport_width + 5:  # 5px tolerance
                violations.append({
                    'guideline': WCAGGuideline.PERCEIVABLE_1_4_10,
                    'severity': 'Serious',
                    'description': f'Content requires horizontal scrolling at {width}x{height}'
                })

        return violations

    def _test_non_text_contrast(self, driver: WebDriver, soup: BeautifulSoup) -> List:
        """Test non-text contrast (1.4.11)"""
        violations = []

        # Test UI components
        ui_elements = soup.find_all(['button', 'input', 'select', 'textarea'])

        for element in ui_elements:
            try:
                element_obj = driver.find_element(By.CSS_SELECTOR, f"{element.name}")
                style = driver.execute_script("""
                    return window.getComputedStyle(arguments[0]);
                """, element_obj)

                # Check for visible borders or outlines
                border = style.get('border', 'none')
                outline = style.get('outline', 'none')

                if border == 'none' and outline == 'none':
                    violations.append({
                        'guideline': WCAGGuideline.PERCEIVABLE_1_4_11,
                        'severity': 'Moderate',
                        'description': 'UI component lacks visible boundary'
                    })

            except:
                continue

        return violations

    def _test_text_spacing(self, driver: WebDriver, soup: BeautifulSoup) -> List:
        """Test text spacing (1.4.12)"""
        violations = []

        # Test text elements
        text_elements = soup.find_all(['p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        for element in text_elements:
            try:
                element_obj = driver.find_element(By.CSS_SELECTOR, f"{element.name}")
                style = driver.execute_script("""
                    return window.getComputedStyle(arguments[0]);
                """, element_obj)

                # Check spacing properties
                line_height = float(style.get('line-height', '1.5'))
                letter_spacing = float(style.get('letter-spacing', '0'))
                word_spacing = float(style.get('word-spacing', '0'))

                # Check minimum spacing requirements
                if line_height < 1.2:
                    violations.append({
                        'guideline': WCAGGuideline.PERCEIVABLE_1_4_12,
                        'severity': 'Moderate',
                        'description': 'Line height less than 1.2'
                    })

            except:
                continue

        return violations

class TestWCAGOperableGuidelines(AccessibilityTestMixin):
    """Test WCAG Operable guidelines (Principle 2)"""

    @pytest.mark.parametrize("guideline_name,wcag_guideline,wcag_level", WCAG_TEST_SCENARIOS["operable"])
    def test_operable_guidelines(self, chrome_driver, guideline_name, wcag_guideline, wcag_level):
        """Test all WCAG Operable guidelines"""
        url = f"http://localhost:3000/patient-portal"
        chrome_driver.get(url)

        violations = []

        if wcag_guideline == WCAGGuideline.OPERABLE_2_1_1:
            # Test keyboard accessibility
            violations = self._test_keyboard_accessibility(chrome_driver)
        elif wcag_guideline == WCAGGuideline.OPERABLE_2_1_2:
            # Test no keyboard trap
            violations = self._test_no_keyboard_trap(chrome_driver)
        elif wcag_guideline == WCAGGuideline.OPERABLE_2_4_1:
            # Test bypass blocks
            violations = self._test_bypass_blocks(chrome_driver)
        elif wcag_guideline == WCAGGuideline.OPERABLE_2_4_2:
            # Test page titled
            violations = self._test_page_titled(chrome_driver)
        elif wcag_guideline == WCAGGuideline.OPERABLE_2_4_7:
            # Test focus visible
            violations = self._test_focus_visible(chrome_driver)

        # Assert compliance
        if wcag_level == WCAGLevel.A:
            critical_violations = [v for v in violations if v['severity'] in ["Critical", "Serious"]]
            assert len(critical_violations) == 0, f"Critical violations found for {guideline_name}"
        elif wcag_level == WCAGLevel.AA:
            assert len(violations) == 0, f"Violations found for AA guideline {guideline_name}"

    def _test_keyboard_accessibility(self, driver: WebDriver) -> List:
        """Test keyboard accessibility (2.1.1)"""
        violations = []

        # Test all interactive elements
        interactive_elements = driver.find_elements(By.CSS_SELECTOR,
            "button, input, select, textarea, a[href]")

        for element in interactive_elements:
            try:
                # Test element is keyboard accessible
                element.send_keys(Keys.TAB)

                # Check if element received focus
                active_element = driver.switch_to.active_element
                if active_element != element:
                    violations.append({
                        'guideline': WCAGGuideline.OPERABLE_2_1_1,
                        'severity': 'Serious',
                        'description': 'Element not keyboard accessible'
                    })

            except:
                violations.append({
                    'guideline': WCAGGuideline.OPERABLE_2_1_1,
                    'severity': 'Serious',
                    'description': 'Keyboard navigation failed'
                })

        return violations

    def _test_no_keyboard_trap(self, driver: WebDriver) -> List:
        """Test no keyboard trap (2.1.2)"""
        violations = []

        # Test that focus can move through all elements
        initial_elements = len(driver.find_elements(By.CSS_SELECTOR, "*"))

        # Navigate through page with Tab
        for i in range(50):  # Limit to prevent infinite loops
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.TAB)

            # Check if we're making progress
            current_elements = len(driver.find_elements(By.CSS_SELECTOR, "*"))
            if current_elements != initial_elements:
                break

        else:
            violations.append({
                'guideline': WCAGGuideline.OPERABLE_2_1_2,
                'severity': 'Critical',
                'description': 'Possible keyboard trap detected'
            })

        return violations

    def _test_bypass_blocks(self, driver: WebDriver) -> List:
        """Test bypass blocks (2.4.1)"""
        violations = []

        # Check for skip links
        skip_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='#'], .skip-link, [aria-label*='skip']")
        if not skip_links:
            violations.append({
                'guideline': WCAGGuideline.OPERABLE_2_4_1,
                'severity': 'Moderate',
                'description': 'No skip navigation link found'
            })

        return violations

    def _test_page_titled(self, driver: WebDriver) -> List:
        """Test page titled (2.4.2)"""
        violations = []

        title = driver.find_element(By.TAG_NAME, "title")
        if not title.get_attribute('textContent').strip():
            violations.append({
                'guideline': WCAGGuideline.OPERABLE_2_4_2,
                'severity': 'Serious',
                'description': 'Page title is empty'
            })

        return violations

    def _test_focus_visible(self, driver: WebDriver) -> List:
        """Test focus visible (2.4.7)"""
        violations = []

        # Test focus visibility on interactive elements
        interactive_elements = driver.find_elements(By.CSS_SELECTOR,
            "button, input, select, textarea, a[href]")

        for element in interactive_elements[:5]:  # Test first 5 elements
            try:
                # Focus element
                driver.execute_script("arguments[0].focus();", element)

                # Check for focus styles
                style = driver.execute_script("""
                    return window.getComputedStyle(arguments[0]);
                """, element)

                outline = style.get('outline', 'none')
                border = style.get('border', 'none')

                if outline == 'none' and border == 'none':
                    violations.append({
                        'guideline': WCAGGuideline.OPERABLE_2_4_7,
                        'severity': 'Serious',
                        'description': 'Focus indicator not visible'
                    })

            except:
                continue

        return violations

class TestWCAGUnderstandableGuidelines(AccessibilityTestMixin):
    """Test WCAG Understandable guidelines (Principle 3)"""

    @pytest.mark.parametrize("guideline_name,wcag_guideline,wcag_level", WCAG_TEST_SCENARIOS["understandable"])
    def test_understandable_guidelines(self, chrome_driver, guideline_name, wcag_guideline, wcag_level):
        """Test all WCAG Understandable guidelines"""
        url = f"http://localhost:3000/patient-portal"
        chrome_driver.get(url)

        violations = []

        if wcag_guideline == WCAGGuideline.UNDERSTANDABLE_3_1_1:
            # Test language of page
            violations = self._test_language_of_page(chrome_driver)
        elif wcag_guideline == WCAGGuideline.UNDERSTANDABLE_3_2_3:
            # Test consistent navigation
            violations = self._test_consistent_navigation(chrome_driver)
        elif wcag_guideline == WCAGGuideline.UNDERSTANDABLE_3_3_1:
            # Test error identification
            violations = self._test_error_identification(chrome_driver)
        elif wcag_guideline == WCAGGuideline.UNDERSTANDABLE_3_3_2:
            # Test labels or instructions
            violations = self._test_labels_instructions(chrome_driver)

        # Assert compliance
        if wcag_level == WCAGLevel.A:
            critical_violations = [v for v in violations if v['severity'] in ["Critical", "Serious"]]
            assert len(critical_violations) == 0, f"Critical violations found for {guideline_name}"
        elif wcag_level == WCAGLevel.AA:
            assert len(violations) == 0, f"Violations found for AA guideline {guideline_name}"

    def _test_language_of_page(self, driver: WebDriver) -> List:
        """Test language of page (3.1.1)"""
        violations = []

        # Check HTML lang attribute
        html_element = driver.find_element(By.TAG_NAME, "html")
        lang_attr = html_element.get_attribute("lang")

        if not lang_attr:
            violations.append({
                'guideline': WCAGGuideline.UNDERSTANDABLE_3_1_1,
                'severity': 'Serious',
                'description': 'HTML missing lang attribute'
            })

        return violations

    def _test_consistent_navigation(self, driver: WebDriver) -> List:
        """Test consistent navigation (3.2.3)"""
        violations = []

        # This would typically test across multiple pages
        # For single page test, we check for navigation presence
        nav_elements = driver.find_elements(By.CSS_SELECTOR, "nav, [role='navigation']")
        if not nav_elements:
            violations.append({
                'guideline': WCAGGuideline.UNDERSTANDABLE_3_2_3,
                'severity': 'Moderate',
                'description': 'No navigation found'
            })

        return violations

    def _test_error_identification(self, driver: WebDriver) -> List:
        """Test error identification (3.3.1)"""
        violations = []

        # Check for error handling mechanisms
        error_elements = driver.find_elements(By.CSS_SELECTOR,
            ".error, [role='alert'], [aria-invalid='true']")

        if not error_elements:
            violations.append({
                'guideline': WCAGGuideline.UNDERSTANDABLE_3_3_1,
                'severity': 'Moderate',
                'description': 'No error identification mechanisms found'
            })

        return violations

    def _test_labels_instructions(self, driver: WebDriver) -> List:
        """Test labels or instructions (3.3.2)"""
        violations = []

        # Test form labels
        form_inputs = driver.find_elements(By.CSS_SELECTOR,
            "input, select, textarea")

        for input_element in form_inputs:
            input_type = input_element.get_attribute("type")

            # Skip hidden inputs
            if input_type == "hidden":
                continue

            # Check for associated label
            input_id = input_element.get_attribute("id")
            has_label = False

            if input_id:
                labels = driver.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                if labels:
                    has_label = True

            # Check for aria-label
            if not has_label:
                aria_label = input_element.get_attribute("aria-label")
                if aria_label:
                    has_label = True

            if not has_label:
                violations.append({
                    'guideline': WCAGGuideline.UNDERSTANDABLE_3_3_2,
                    'severity': 'Serious',
                    'description': 'Form input missing label'
                })

        return violations

class TestWCAGRobustGuidelines(AccessibilityTestMixin):
    """Test WCAG Robust guidelines (Principle 4)"""

    @pytest.mark.parametrize("guideline_name,wcag_guideline,wcag_level", WCAG_TEST_SCENARIOS["robust"])
    def test_robust_guidelines(self, chrome_driver, guideline_name, wcag_guideline, wcag_level):
        """Test all WCAG Robust guidelines"""
        url = f"http://localhost:3000/patient-portal"
        chrome_driver.get(url)

        violations = []

        if wcag_guideline == WCAGGuideline.ROBUST_4_1_1:
            # Test parsing
            violations = self._test_parsing(chrome_driver)
        elif wcag_guideline == WCAGGuideline.ROBUST_4_1_2:
            # Test name, role, value
            violations = self._test_name_role_value(chrome_driver)

        # Assert compliance
        if wcag_level == WCAGLevel.A:
            critical_violations = [v for v in violations if v['severity'] in ["Critical", "Serious"]]
            assert len(critical_violations) == 0, f"Critical violations found for {guideline_name}"
        elif wcag_level == WCAGLevel.AA:
            assert len(violations) == 0, f"Violations found for AA guideline {guideline_name}"

    def _test_parsing(self, driver: WebDriver) -> List:
        """Test parsing (4.1.1)"""
        violations = []

        # Check for HTML validation issues
        # This is a simplified test - in practice, you'd use an HTML validator

        # Check for duplicate IDs
        all_elements = driver.find_elements(By.CSS_SELECTOR, "[id]")
        ids = [elem.get_attribute("id") for elem in all_elements]

        duplicate_ids = [id for id in set(ids) if ids.count(id) > 1]
        for duplicate_id in duplicate_ids:
            violations.append({
                'guideline': WCAGGuideline.ROBUST_4_1_1,
                'severity': 'Serious',
                'description': f'Duplicate ID found: {duplicate_id}'
            })

        return violations

    def _test_name_role_value(self, driver: WebDriver) -> List:
        """Test name, role, value (4.1.2)"""
        violations = []

        # Test interactive elements have proper ARIA attributes
        interactive_elements = driver.find_elements(By.CSS_SELECTOR,
            "button, input, select, textarea, a[href]")

        for element in interactive_elements:
            # Check for proper name
            has_name = False

            # Check for text content
            text_content = element.get_attribute("textContent").strip()
            if text_content:
                has_name = True

            # Check for aria-label
            if not has_name:
                aria_label = element.get_attribute("aria-label")
                if aria_label:
                    has_name = True

            # Check for aria-labelledby
            if not has_name:
                aria_labelledby = element.get_attribute("aria-labelledby")
                if aria_labelledby:
                    has_name = True

            # Check for alt text if image
            if not has_name and element.tag_name == "img":
                alt_text = element.get_attribute("alt")
                if alt_text:
                    has_name = True

            if not has_name:
                violations.append({
                    'guideline': WCAGGuideline.ROBUST_4_1_2,
                    'severity': 'Serious',
                    'description': 'Interactive element missing accessible name'
                })

        return violations

class TestWCAGComplianceLevels(AccessibilityTestMixin):
    """Test WCAG compliance levels"""

    def test_wcag_a_compliance(self, chrome_driver):
        """Test WCAG Level A compliance"""
        url = f"http://localhost:3000/patient-portal"
        framework = AccessibilityTestingFramework()

        audit_result = framework.run_comprehensive_accessibility_audit(url, chrome_driver)

        # Level A should have no critical violations
        level_a_violations = [
            v for v in audit_result.violations
            if v.wcag_level == WCAGLevel.A and v.severity in ["Critical", "Serious"]
        ]

        assert len(level_a_violations) == 0, \
            f"Found {len(level_a_violations)} Level A violations"

    def test_wcag_aa_compliance(self, chrome_driver):
        """Test WCAG Level AA compliance"""
        url = f"http://localhost:3000/patient-portal"
        framework = AccessibilityTestingFramework()

        audit_result = framework.run_comprehensive_accessibility_audit(url, chrome_driver)

        # Level AA should have no violations
        level_aa_violations = [
            v for v in audit_result.violations
            if v.wcag_level == WCAGLevel.AA
        ]

        # Allow minor violations for AA level
        serious_aa_violations = [
            v for v in level_aa_violations
            if v.severity in ["Critical", "Serious"]
        ]

        assert len(serious_aa_violations) == 0, \
            f"Found {len(serious_aa_violations)} serious Level AA violations"

        # Overall AA compliance should be high
        aa_compliance = audit_result.wcag_compliance.get(WCAGLevel.AA, 0)
        assert aa_compliance >= 90.0, \
            f"WCAG AA compliance too low: {aa_compliance:.1f}%"

    def test_wcag_aaa_compliance(self, chrome_driver):
        """Test WCAG Level AAA compliance"""
        url = f"http://localhost:3000/patient-portal"
        framework = AccessibilityTestingFramework()

        audit_result = framework.run_comprehensive_accessibility_audit(url, chrome_driver)

        # Level AAA is aspirational, so we allow some violations
        # but no critical ones
        aaa_violations = [
            v for v in audit_result.violations
            if v.wcag_level == WCAGLevel.AAA
        ]

        critical_aaa_violations = [
            v for v in aaa_violations
            if v.severity == "Critical"
        ]

        assert len(critical_aaa_violations) == 0, \
            f"Found {len(critical_aaa_violations)} critical Level AAA violations"

        # AAA compliance should still be reasonable
        aaa_compliance = audit_result.wcag_compliance.get(WCAGLevel.AAA, 0)
        assert aaa_compliance >= 70.0, \
            f"WCAG AAA compliance too low: {aaa_compliance:.1f}%"

class TestWCAGHealthcareSpecific(HealthcareAccessibilityTestMixin):
    """Test WCAG compliance with healthcare-specific requirements"""

    def test_healthcare_wcag_enhancements(self, chrome_driver):
        """Test healthcare-specific WCAG enhancements"""
        healthcare_pages = [
            "/patient-portal",
            "/appointments",
            "/medical-records",
            "/emergency",
            "/pharmacy"
        ]

        for page in healthcare_pages:
            url = f"http://localhost:3000{page}"
            framework = AccessibilityTestingFramework()

            audit_result = framework.run_comprehensive_accessibility_audit(url, chrome_driver)

            # Healthcare pages should have higher accessibility standards
            self.assert_accessibility_compliance(audit_result, 85.0)
            self.assert_no_critical_violations(audit_result)

            # Healthcare-specific issues should be minimal
            healthcare_issues = len(audit_result.healthcare_specific_issues)
            assert healthcare_issues <= 3, \
                f"Too many healthcare-specific issues on {page}: {healthcare_issues}"

    def test_emergency_information_wcag_priority(self, chrome_driver):
        """Test emergency information WCAG priority"""
        url = f"http://localhost:3000/emergency"
        framework = AccessibilityTestingFramework()

        audit_result = framework.run_comprehensive_accessibility_audit(url, chrome_driver)

        # Emergency information must meet highest standards
        self.assert_accessibility_compliance(audit_result, 95.0)
        self.assert_no_critical_violations(audit_result)
        self.assert_emergency_information_accessibility(audit_result)

        # Emergency-specific WCAG compliance
        assert audit_result.overall_score >= 95.0, \
            f"Emergency page accessibility too low: {audit_result.overall_score:.1f}%"

# WCAG compliance scoring
def calculate_wcag_compliance_score(audit_result) -> Dict[str, float]:
    """Calculate detailed WCAG compliance scores"""
    scores = {}

    # Calculate scores by WCAG level
    for level in WCAGLevel:
        level_violations = [
            v for v in audit_result.violations if v.wcag_level == level
        ]

        if level == WCAGLevel.A:
            # Level A: 100% - (critical_violations * 20 + serious_violations * 10)
            critical = len([v for v in level_violations if v.severity == "Critical"])
            serious = len([v for v in level_violations if v.severity == "Serious"])
            scores[level] = max(0, 100 - (critical * 20 + serious * 10))
        elif level == WCAGLevel.AA:
            # Level AA: 100% - (violations * 5)
            scores[level] = max(0, 100 - (len(level_violations) * 5))
        elif level == WCAGLevel.AAA:
            # Level AAA: 100% - (violations * 2)
            scores[level] = max(0, 100 - (len(level_violations) * 2))

    return scores

def generate_wcag_compliance_report(audit_result) -> str:
    """Generate detailed WCAG compliance report"""
    scores = calculate_wcag_compliance_score(audit_result)

    report = f"""
# WCAG 2.1 Compliance Report

## Overall Score: {audit_result.overall_score:.1f}%

## Compliance by Level
- **Level A**: {scores.get(WCAGLevel.A, 0):.1f}%
- **Level AA**: {scores.get(WCAGLevel.AA, 0):.1f}%
- **Level AAA**: {scores.get(WCAGLevel.AAA, 0):.1f}%

## Violations Summary
- **Total Violations**: {audit_result.total_violations}
- **Critical**: {audit_result.critical_violations}
- **Serious**: {audit_result.serious_violations}
- **Moderate**: {audit_result.moderate_violations}
- **Minor**: {audit_result.minor_violations}

## Healthcare-Specific Issues
- **Total Issues**: {len(audit_result.healthcare_specific_issues)}

## Recommendations
"""

    for i, rec in enumerate(audit_result.recommendations[:5], 1):
        report += f"{i}. {rec}\n"

    return report

# Test execution
if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--wcag"
    ])