"""
Comprehensive Accessibility Testing Framework for HMS System
Provides WCAG 2.1 AA and AAA compliance testing with healthcare-specific accessibility validation
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
from urllib.parse import urljoin

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
import requests
from bs4 import BeautifulSoup
from PIL import Image
import cv2
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WCAGGuideline(Enum):
    """WCAG 2.1 Guidelines and Success Criteria"""
    # Perceivable
    PERCEIVABLE_1_1_1 = "1.1.1 Non-text Content"  # Level A
    PERCEIVABLE_1_2_1 = "1.2.1 Audio-only and Video-only"  # Level A
    PERCEIVABLE_1_2_2 = "1.2.2 Captions"  # Level A
    PERCEIVABLE_1_2_3 = "1.2.3 Audio Description or Media Alternative"  # Level A
    PERCEIVABLE_1_2_4 = "1.2.4 Captions (Live)"  # Level AA
    PERCEIVABLE_1_2_5 = "1.2.5 Audio Description"  # Level AA
    PERCEIVABLE_1_3_1 = "1.3.1 Info and Relationships"  # Level A
    PERCEIVABLE_1_3_2 = "1.3.2 Meaningful Sequence"  # Level A
    PERCEIVABLE_1_3_3 = "1.3.3 Sensory Characteristics"  # Level A
    PERCEIVABLE_1_3_4 = "1.3.4 Orientation"  # Level AA
    PERCEIVABLE_1_3_5 = "1.3.5 Identify Input Purpose"  # Level AA
    PERCEIVABLE_1_3_6 = "1.3.6 Identify Purpose"  # Level AAA
    PERCEIVABLE_1_4_1 = "1.4.1 Use of Color"  # Level A
    PERCEIVABLE_1_4_2 = "1.4.2 Audio Control"  # Level A
    PERCEIVABLE_1_4_3 = "1.4.3 Contrast (Minimum)"  # Level AA
    PERCEIVABLE_1_4_4 = "1.4.4 Resize text"  # Level AA
    PERCEIVABLE_1_4_5 = "1.4.5 Images of Text"  # Level AA
    PERCEIVABLE_1_4_6 = "1.4.6 Contrast (Enhanced)"  # Level AAA
    PERCEIVABLE_1_4_7 = "1.4.7 Low or No Background Audio"  # Level AAA
    PERCEIVABLE_1_4_8 = "1.4.8 Visual Presentation"  # Level AAA
    PERCEIVABLE_1_4_9 = "1.4.9 Images of Text (No Exception)"  # Level AAA
    PERCEIVABLE_1_4_10 = "1.4.10 Reflow"  # Level AA
    PERCEIVABLE_1_4_11 = "1.4.11 Non-text Contrast"  # Level AA
    PERCEIVABLE_1_4_12 = "1.4.12 Text Spacing"  # Level AA
    PERCEIVABLE_1_4_13 = "1.4.13 Content on Hover or Focus"  # Level AA

    # Operable
    OPERABLE_2_1_1 = "2.1.1 Keyboard"  # Level A
    OPERABLE_2_1_2 = "2.1.2 No Keyboard Trap"  # Level A
    OPERABLE_2_1_3 = "2.1.3 Keyboard (No Exception)"  # Level AAA
    OPERABLE_2_1_4 = "2.1.4 Character Key Shortcuts"  # Level A
    OPERABLE_2_2_1 = "2.2.1 Timing Adjustable"  # Level A
    OPERABLE_2_2_2 = "2.2.2 Pause, Stop, Hide"  # Level A
    OPERABLE_2_3_1 = "2.3.1 Three Flashes or Below Threshold"  # Level A
    OPERABLE_2_4_1 = "2.4.1 Bypass Blocks"  # Level A
    OPERABLE_2_4_2 = "2.4.2 Page Titled"  # Level A
    OPERABLE_2_4_3 = "2.4.3 Focus Order"  # Level A
    OPERABLE_2_4_4 = "2.4.4 Link Purpose (In Context)"  # Level A
    OPERABLE_2_4_5 = "2.4.5 Multiple Ways"  # Level AA
    OPERABLE_2_4_6 = "2.4.6 Headings and Labels"  # Level AA
    OPERABLE_2_4_7 = "2.4.7 Focus Visible"  # Level AA
    OPERABLE_2_5_1 = "2.5.1 Pointer Gestures"  # Level A
    OPERABLE_2_5_2 = "2.5.2 Pointer Cancellation"  # Level A
    OPERABLE_2_5_3 = "2.5.3 Label in Name"  # Level A
    OPERABLE_2_5_4 = "2.5.4 Motion Actuation"  # Level A
    OPERABLE_2_5_5 = "2.5.5 Target Size"  # Level AAA
    OPERABLE_2_5_6 = "2.5.6 Concurrent Input Mechanisms"  # Level AAA

    # Understandable
    UNDERSTANDABLE_3_1_1 = "3.1.1 Language of Page"  # Level A
    UNDERSTANDABLE_3_1_2 = "3.1.2 Language of Parts"  # Level AA
    UNDERSTANDABLE_3_2_1 = "3.2.1 On Focus"  # Level A
    UNDERSTANDABLE_3_2_2 = "3.2.2 On Input"  # Level A
    UNDERSTANDABLE_3_2_3 = "3.2.3 Consistent Navigation"  # Level AA
    UNDERSTANDABLE_3_2_4 = "3.2.4 Consistent Identification"  # Level AA
    UNDERSTANDABLE_3_3_1 = "3.3.1 Error Identification"  # Level A
    UNDERSTANDABLE_3_3_2 = "3.3.2 Labels or Instructions"  # Level A
    UNDERSTANDABLE_3_3_3 = "3.3.3 Error Suggestion"  # Level AA
    UNDERSTANDABLE_3_3_4 = "3.3.4 Error Prevention"  # Level AA

    # Robust
    ROBUST_4_1_1 = "4.1.1 Parsing"  # Level A
    ROBUST_4_1_2 = "4.1.2 Name, Role, Value"  # Level A
    ROBUST_4_1_3 = "4.1.3 Status Messages"  # Level AA

class WCAGLevel(Enum):
    """WCAG Conformance Levels"""
    A = "A"      # Essential for some users to access the web
    AA = "AA"    # Addresses major barriers
    AAA = "AAA"  # Enhanced accessibility for optimal user experience

class AccessibilityViolationType(Enum):
    """Types of accessibility violations"""
    MISSING_ALT_TEXT = "Missing Alt Text"
    LOW_CONTRAST = "Low Contrast"
    MISSING_LABEL = "Missing Label"
    INVALID_HTML = "Invalid HTML"
    MISSING_FOCUS_INDICATOR = "Missing Focus Indicator"
    MISSING_LANDMARK = "Missing Landmark"
    MISSING_HEADING = "Missing Heading"
    MISSING_LANG_ATTR = "Missing Language Attribute"
    MISSING_TITLE = "Missing Page Title"
    MISSING_SKIP_LINK = "Missing Skip Link"
    INVALID_TABLE = "Invalid Table Structure"
    MISSING_FORM_LABEL = "Missing Form Label"
    MISSING_ERROR_MESSAGE = "Missing Error Message"
    MISSING_CAPTION = "Missing Caption"
    MISSING_AUDIO_DESCRIPTION = "Missing Audio Description"
    MISSING_TRANSITION = "Missing Transition"
    MISSING_RESIZE = "Missing Resize Option"
    MISSING_FOCUS_VISIBLE = "Missing Focus Visible"
    MISSING_REFLOW = "Missing Reflow Support"
    MISSING_TEXT_SPACING = "Missing Text Spacing"
    MISSING_CONTENT_ON_HOVER = "Missing Content on Hover/Focus"
    MISSING_KEYBOARD_NAVIGATION = "Missing Keyboard Navigation"
    MISSING_KEYBOARD_TRAP = "Keyboard Trap Detected"
    MISSING_POINTER_GESTURES = "Missing Pointer Gestures Support"
    MISSING_POINTER_CANCELLATION = "Missing Pointer Cancellation"
    MISSING_LABEL_IN_NAME = "Missing Label in Name"
    MISSING_MOTION_ACTUATION = "Missing Motion Actuation"
    MISSING_CONCURRENT_INPUT = "Missing Concurrent Input"
    MISSING_LANGUAGE_OF_PARTS = "Missing Language of Parts"
    MISSING_CONSISTENT_NAVIGATION = "Missing Consistent Navigation"
    MISSING_CONSISTENT_IDENTIFICATION = "Missing Consistent Identification"
    MISSING_ERROR_SUGGESTION = "Missing Error Suggestion"
    MISSING_ERROR_PREVENTION = "Missing Error Prevention"
    MISSING_PARSING = "Missing Valid HTML Parsing"
    MISSING_NAME_ROLE_VALUE = "Missing Name, Role, Value"
    MISSING_STATUS_MESSAGES = "Missing Status Messages"
    MISSING_SCREEN_READER_COMPATIBILITY = "Screen Reader Compatibility Issues"
    MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY = "Healthcare-Specific Accessibility Issues"

@dataclass
class AccessibilityTestResult:
    """Accessibility test result"""
    guideline: WCAGGuideline
    violation_type: AccessibilityViolationType
    element: str
    element_selector: str
    severity: str  # "Critical", "Serious", "Moderate", "Minor"
    description: str
    recommendation: str
    wcag_level: WCAGLevel
    impact: str  # "High", "Medium", "Low"
    screenshot: Optional[str] = None
    element_code: Optional[str] = None
    page_url: Optional[str] = None

@dataclass
class AccessibilityAuditResult:
    """Complete accessibility audit result"""
    page_url: str
    timestamp: float
    total_violations: int
    critical_violations: int
    serious_violations: int
    moderate_violations: int
    minor_violations: int
    violations: List[AccessibilityTestResult]
    wcag_compliance: Dict[WCAGLevel, float]  # Compliance percentage by level
    healthcare_specific_issues: List[AccessibilityTestResult]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]
    overall_score: float

class AccessibilityTestingFramework:
    """Comprehensive accessibility testing framework"""

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.violations: List[AccessibilityTestResult] = []
        self.healthcare_violations: List[AccessibilityTestResult] = []
        self.performance_metrics = {}

        # Initialize accessibility testing tools
        self.contrast_thresholds = {
            'normal_text': {'small': 4.5, 'large': 3.0},
            'ui_components': {'small': 3.0, 'large': 3.0},
            'graphics': {'small': 3.0, 'large': 3.0}
        }

        # Healthcare-specific accessibility requirements
        self.healthcare_requirements = {
            'high_contrast_mode': True,
            'screen_reader_compatibility': True,
            'keyboard_navigation': True,
            'font_size_adjustment': True,
            'color_blind_friendly': True,
            'seizure_safe': True,
            'responsive_for_disabilities': True,
            'medical_data_accessibility': True,
            'emergency_accessibility': True,
            'medication_information_accessibility': True
        }

    def run_comprehensive_accessibility_audit(self, page_url: str, driver: Optional[WebDriver] = None) -> AccessibilityAuditResult:
        """Run comprehensive accessibility audit"""
        logger.info(f"Starting comprehensive accessibility audit for: {page_url}")

        start_time = time.time()
        self.violations = []
        self.healthcare_violations = []

        if driver is None:
            # Create WebDriver for testing
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=options)

        try:
            driver.get(page_url)

            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Get page source for analysis
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Run all accessibility tests
            self._test_wcag_perceivable_guidelines(driver, soup, page_url)
            self._test_wcag_operable_guidelines(driver, soup, page_url)
            self._test_wcag_understandable_guidelines(driver, soup, page_url)
            self._test_wcag_robust_guidelines(driver, soup, page_url)

            # Healthcare-specific accessibility tests
            self._test_healthcare_specific_accessibility(driver, soup, page_url)

            # Calculate compliance metrics
            compliance_scores = self._calculate_wcag_compliance()

            # Generate performance metrics
            self.performance_metrics = {
                'test_duration': time.time() - start_time,
                'total_elements_tested': len(soup.find_all(True)),
                'interactive_elements_tested': len(soup.find_all(['button', 'input', 'select', 'textarea', 'a'])),
                'forms_tested': len(soup.find_all('form')),
                'tables_tested': len(soup.find_all('table')),
                'images_tested': len(soup.find_all('img')),
                'videos_tested': len(soup.find_all(['video', 'audio']))
            }

            # Generate recommendations
            recommendations = self._generate_recommendations()

            # Calculate overall score
            overall_score = self._calculate_overall_score()

            # Categorize violations
            critical = [v for v in self.violations if v.severity == "Critical"]
            serious = [v for v in self.violations if v.severity == "Serious"]
            moderate = [v for v in self.violations if v.severity == "Moderate"]
            minor = [v for v in self.violations if v.severity == "Minor"]

            result = AccessibilityAuditResult(
                page_url=page_url,
                timestamp=time.time(),
                total_violations=len(self.violations),
                critical_violations=len(critical),
                serious_violations=len(serious),
                moderate_violations=len(moderate),
                minor_violations=len(minor),
                violations=self.violations,
                wcag_compliance=compliance_scores,
                healthcare_specific_issues=self.healthcare_violations,
                performance_metrics=self.performance_metrics,
                recommendations=recommendations,
                overall_score=overall_score
            )

            logger.info(f"Accessibility audit completed. Score: {overall_score:.1f}%")
            return result

        finally:
            if driver:
                driver.quit()

    def _test_wcag_perceivable_guidelines(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test WCAG Perceivable guidelines"""
        logger.info("Testing WCAG Perceivable guidelines")

        # 1.1.1 Non-text Content (Alt text)
        self._test_alt_text(soup, page_url)

        # 1.2.1-1.2.5 Time-based Media
        self._test_time_based_media(soup, page_url)

        # 1.3.1-1.3.6 Adaptable
        self._test_adaptable_content(driver, soup, page_url)

        # 1.4.1-1.4.13 Distinguishable
        self._test_distinguishable_content(driver, soup, page_url)

    def _test_wcag_operable_guidelines(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test WCAG Operable guidelines"""
        logger.info("Testing WCAG Operable guidelines")

        # 2.1.1-2.1.4 Keyboard Accessible
        self._test_keyboard_accessibility(driver, soup, page_url)

        # 2.2.1-2.2.2 Enough Time
        self._test_timing_controls(driver, soup, page_url)

        # 2.3.1 Seizures
        self._test_seizure_controls(soup, page_url)

        # 2.4.1-2.4.12 Navigable
        self._test_navigation_structure(driver, soup, page_url)

        # 2.5.1-2.5.6 Input Modalities
        self._test_input_modalities(driver, soup, page_url)

    def _test_wcag_understandable_guidelines(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test WCAG Understandable guidelines"""
        logger.info("Testing WCAG Understandable guidelines")

        # 3.1.1-3.1.2 Readable
        self._test_readable_content(soup, page_url)

        # 3.2.1-3.2.4 Predictable
        self._test_predictable_content(driver, soup, page_url)

        # 3.3.1-3.3.4 Input Assistance
        self._test_input_assistance(driver, soup, page_url)

    def _test_wcag_robust_guidelines(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test WCAG Robust guidelines"""
        logger.info("Testing WCAG Robust guidelines")

        # 4.1.1-4.1.3 Compatible
        self._test_compatibility(driver, soup, page_url)

    def _test_healthcare_specific_accessibility(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test healthcare-specific accessibility requirements"""
        logger.info("Testing healthcare-specific accessibility")

        # High contrast mode for medical data
        self._test_high_contrast_mode(driver, page_url)

        # Screen reader compatibility for medical information
        self._test_screen_reader_compatibility(soup, page_url)

        # Emergency information accessibility
        self._test_emergency_accessibility(soup, page_url)

        # Medication information accessibility
        self._test_medication_accessibility(soup, page_url)

        # Medical form accessibility
        self._test_medical_form_accessibility(driver, soup, page_url)

        # Appointment scheduling accessibility
        self._test_appointment_accessibility(driver, soup, page_url)

        # Lab results accessibility
        self._test_lab_results_accessibility(soup, page_url)

        # Billing information accessibility
        self._test_billing_accessibility(soup, page_url)

    def _test_alt_text(self, soup: BeautifulSoup, page_url: str):
        """Test alt text for images"""
        images = soup.find_all('img')
        for img in images:
            if not img.get('alt'):
                violation = AccessibilityTestResult(
                    guideline=WCAGGuideline.PERCEIVABLE_1_1_1,
                    violation_type=AccessibilityViolationType.MISSING_ALT_TEXT,
                    element=f"Image: {img.get('src', 'unknown')}",
                    element_selector=f"img[src='{img.get('src', '')}']",
                    severity="Serious",
                    description="Image missing alt text",
                    recommendation="Add descriptive alt text to all images",
                    wcag_level=WCAGLevel.A,
                    impact="High",
                    page_url=page_url
                )
                self.violations.append(violation)

    def _test_contrast_ratio(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test color contrast ratios"""
        # This would typically use a color contrast library
        # For now, we'll check for common contrast issues
        text_elements = soup.find_all(['p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        for element in text_elements:
            style = element.get('style', '')
            if 'color' in style and 'background-color' in style:
                # Check for obvious low contrast combinations
                violation = AccessibilityTestResult(
                    guideline=WCAGGuideline.PERCEIVABLE_1_4_3,
                    violation_type=AccessibilityViolationType.LOW_CONTRAST,
                    element=f"Text element: {element.get_text()[:50]}...",
                    element_selector=str(element.name),
                    severity="Serious",
                    description="Potential low contrast text",
                    recommendation="Ensure text has sufficient contrast with background (4.5:1 for normal text, 3:1 for large text)",
                    wcag_level=WCAGLevel.AA,
                    impact="High",
                    page_url=page_url
                )
                self.violations.append(violation)

    def _test_keyboard_accessibility(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test keyboard navigation and accessibility"""
        interactive_elements = soup.find_all(['button', 'input', 'select', 'textarea', 'a'])

        # Test focus order
        try:
            # Test Tab navigation
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.TAB)

            # Check if focus is visible
            active_element = driver.switch_to.active_element
            if not self._has_visible_focus(driver, active_element):
                violation = AccessibilityTestResult(
                    guideline=WCAGGuideline.OPERABLE_2_4_7,
                    violation_type=AccessibilityViolationType.MISSING_FOCUS_VISIBLE,
                    element="Interactive element",
                    element_selector="body",
                    severity="Serious",
                    description="Focus indicator not visible",
                    recommendation="Ensure focus is clearly visible on all interactive elements",
                    wcag_level=WCAGLevel.AA,
                    impact="High",
                    page_url=page_url
                )
                self.violations.append(violation)

        except Exception as e:
            logger.warning(f"Keyboard navigation test failed: {e}")

    def _test_form_labels(self, soup: BeautifulSoup, page_url: str):
        """Test form labels and accessibility"""
        form_inputs = soup.find_all(['input', 'select', 'textarea'])

        for form_input in form_inputs:
            input_type = form_input.get('type', 'text')

            # Skip hidden inputs and submit buttons
            if input_type in ['hidden', 'submit']:
                continue

            # Check for associated label
            input_id = form_input.get('id')
            has_label = False

            if input_id:
                labels = soup.find_all('label', {'for': input_id})
                if labels:
                    has_label = True

            # Check for aria-label if no label found
            if not has_label:
                aria_label = form_input.get('aria-label')
                if aria_label:
                    has_label = True

            if not has_label:
                violation = AccessibilityTestResult(
                    guideline=WCAGGuideline.OPERABLE_3_3_2,
                    violation_type=AccessibilityViolationType.MISSING_FORM_LABEL,
                    element=f"Form input: {form_input.get('name', 'unnamed')}",
                    element_selector=str(form_input.name),
                    severity="Serious",
                    description="Form input missing label",
                    recommendation="Add proper label association using 'for' attribute or aria-label",
                    wcag_level=WCAGLevel.A,
                    impact="High",
                    page_url=page_url
                )
                self.violations.append(violation)

    def _test_heading_structure(self, soup: BeautifulSoup, page_url: str):
        """Test heading hierarchy and structure"""
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        # Check for heading order violations
        previous_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if level > previous_level + 1:
                violation = AccessibilityTestResult(
                    guideline=WCAGGuideline.OPERABLE_2_4_6,
                    violation_type=AccessibilityViolationType.MISSING_HEADING,
                    element=f"Heading: {heading.get_text()[:50]}...",
                    element_selector=str(heading.name),
                    severity="Moderate",
                    description=f"Heading level {level} follows level {previous_level} without intermediate heading",
                    recommendation="Maintain proper heading hierarchy (h1, h2, h3, etc.)",
                    wcag_level=WCAGLevel.AA,
                    impact="Medium",
                    page_url=page_url
                )
                self.violations.append(violation)
            previous_level = level

    def _test_landmark_regions(self, soup: BeautifulSoup, page_url: str):
        """Test landmark regions for navigation"""
        # Check for common landmark regions
        landmarks = ['header', 'nav', 'main', 'footer', 'aside', 'section']
        found_landmarks = set()

        for landmark in landmarks:
            elements = soup.find_all(landmark)
            if elements:
                found_landmarks.add(landmark)

        # Check for main content area
        if 'main' not in found_landmarks:
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.OPERABLE_2_4_1,
                violation_type=AccessibilityViolationType.MISSING_LANDMARK,
                element="Main content area",
                element_selector="body",
                severity="Serious",
                description="Missing main landmark region",
                recommendation="Add <main> landmark for main content area",
                wcag_level=WCAGLevel.A,
                impact="High",
                page_url=page_url
            )
            self.violations.append(violation)

    def _test_language_attributes(self, soup: BeautifulSoup, page_url: str):
        """Test language attributes"""
        html_tag = soup.find('html')
        if not html_tag or not html_tag.get('lang'):
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.UNDERSTANDABLE_3_1_1,
                violation_type=AccessibilityViolationType.MISSING_LANG_ATTR,
                element="HTML document",
                element_selector="html",
                severity="Serious",
                description="Missing language attribute",
                recommendation="Add lang attribute to HTML tag (e.g., lang='en')",
                wcag_level=WCAGLevel.A,
                impact="High",
                page_url=page_url
            )
            self.violations.append(violation)

    def _test_page_title(self, soup: BeautifulSoup, page_url: str):
        """Test page title"""
        title = soup.find('title')
        if not title or not title.get_text().strip():
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.OPERABLE_2_4_2,
                violation_type=AccessibilityViolationType.MISSING_TITLE,
                element="Page title",
                element_selector="title",
                severity="Serious",
                description="Missing page title",
                recommendation="Add descriptive title to each page",
                wcag_level=WCAGLevel.A,
                impact="High",
                page_url=page_url
            )
            self.violations.append(violation)

    def _test_table_accessibility(self, soup: BeautifulSoup, page_url: str):
        """Test table accessibility"""
        tables = soup.find_all('table')

        for table in tables:
            # Check for caption
            caption = table.find('caption')
            if not caption:
                violation = AccessibilityTestResult(
                    guideline=WCAGGuideline.PERCEIVABLE_1_3_1,
                    violation_type=AccessibilityViolationType.MISSING_CAPTION,
                    element="Table",
                    element_selector="table",
                    severity="Moderate",
                    description="Table missing caption",
                    recommendation="Add caption to describe table purpose",
                    wcag_level=WCAGLevel.A,
                    impact="Medium",
                    page_url=page_url
                )
                self.violations.append(violation)

            # Check for proper headers
            headers = table.find_all('th')
            if not headers:
                violation = AccessibilityTestResult(
                    guideline=WCAGGuideline.PERCEIVABLE_1_3_1,
                    violation_type=AccessibilityViolationType.INVALID_TABLE,
                    element="Table headers",
                    element_selector="table",
                    severity="Serious",
                    description="Table missing header cells",
                    recommendation="Use <th> for header cells with scope attribute",
                    wcag_level=WCAGLevel.A,
                    impact="High",
                    page_url=page_url
                )
                self.violations.append(violation)

    def _test_healthcare_specific_accessibility_detailed(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test healthcare-specific accessibility requirements"""

        # Test emergency information accessibility
        emergency_elements = soup.find_all(class_=lambda x: x and 'emergency' in x.lower())
        for element in emergency_elements:
            # Check if emergency information is accessible
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.PERCEIVABLE_1_4_3,
                violation_type=AccessibilityViolationType.MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY,
                element=f"Emergency information: {element.get_text()[:50]}...",
                element_selector=str(element.name),
                severity="Critical",
                description="Emergency information may not be accessible",
                recommendation="Ensure emergency information is highly visible and accessible",
                wcag_level=WCAGLevel.AA,
                impact="Critical",
                page_url=page_url
            )
            self.healthcare_violations.append(violation)

        # Test medication information accessibility
        medication_elements = soup.find_all(class_=lambda x: x and 'medication' in x.lower())
        for element in medication_elements:
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.OPERABLE_2_4_6,
                violation_type=AccessibilityViolationType.MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY,
                element=f"Medication information: {element.get_text()[:50]}...",
                element_selector=str(element.name),
                severity="Serious",
                description="Medication information may not be properly labeled",
                recommendation="Ensure medication information is clearly labeled and accessible",
                wcag_level=WCAGLevel.AA,
                impact="High",
                page_url=page_url
            )
            self.healthcare_violations.append(violation)

    def _test_high_contrast_mode(self, driver: WebDriver, page_url: str):
        """Test high contrast mode for medical data"""
        try:
            # Check if page supports high contrast mode
            # This is a simplified test - in practice, you'd test actual contrast modes
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.PERCEIVABLE_1_4_6,
                violation_type=AccessibilityViolationType.MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY,
                element="High contrast mode",
                element_selector="body",
                severity="Serious",
                description="High contrast mode not explicitly supported",
                recommendation="Implement high contrast mode for medical data visibility",
                wcag_level=WCAGLevel.AAA,
                impact="High",
                page_url=page_url
            )
            self.healthcare_violations.append(violation)
        except Exception as e:
            logger.warning(f"High contrast test failed: {e}")

    def _test_screen_reader_compatibility(self, soup: BeautifulSoup, page_url: str):
        """Test screen reader compatibility"""
        # Check for ARIA labels and roles
        interactive_elements = soup.find_all(['button', 'input', 'select', 'textarea'])

        for element in interactive_elements:
            if not element.get('aria-label') and not element.get('aria-labelledby'):
                violation = AccessibilityTestResult(
                    guideline=WCAGGuideline.ROBUST_4_1_2,
                    violation_type=AccessibilityViolationType.MISSING_SCREEN_READER_COMPATIBILITY,
                    element=f"Interactive element: {element.get('name', 'unnamed')}",
                    element_selector=str(element.name),
                    severity="Serious",
                    description="Element may not be screen reader compatible",
                    recommendation="Add ARIA labels or ensure proper label association",
                    wcag_level=WCAGLevel.A,
                    impact="High",
                    page_url=page_url
                )
                self.healthcare_violations.append(violation)

    def _test_emergency_accessibility(self, soup: BeautifulSoup, page_url: str):
        """Test emergency information accessibility"""
        emergency_elements = soup.find_all(class_=lambda x: x and 'emergency' in x.lower())

        for element in emergency_elements:
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.PERCEIVABLE_1_4_3,
                violation_type=AccessibilityViolationType.MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY,
                element=f"Emergency information: {element.get_text()[:50]}...",
                element_selector=str(element.name),
                severity="Critical",
                description="Emergency information accessibility not verified",
                recommendation="Ensure emergency information is accessible and visible",
                wcag_level=WCAGLevel.AA,
                impact="Critical",
                page_url=page_url
            )
            self.healthcare_violations.append(violation)

    def _test_medication_accessibility(self, soup: BeautifulSoup, page_url: str):
        """Test medication information accessibility"""
        medication_elements = soup.find_all(class_=lambda x: x and 'medication' in x.lower())

        for element in medication_elements:
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.OPERABLE_2_4_6,
                violation_type=AccessibilityViolationType.MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY,
                element=f"Medication information: {element.get_text()[:50]}...",
                element_selector=str(element.name),
                severity="Serious",
                description="Medication information accessibility not verified",
                recommendation="Ensure medication information is clearly labeled and accessible",
                wcag_level=WCAGLevel.AA,
                impact="High",
                page_url=page_url
            )
            self.healthcare_violations.append(violation)

    def _test_medical_form_accessibility(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test medical form accessibility"""
        forms = soup.find_all('form')

        for form in forms:
            form_class = form.get('class', [])
            if any('medical' in str(cls).lower() for cls in form_class):
                violation = AccessibilityTestResult(
                    guideline=WCAGGuideline.OPERABLE_3_3_2,
                    violation_type=AccessibilityViolationType.MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY,
                    element="Medical form",
                    element_selector="form",
                    severity="Serious",
                    description="Medical form accessibility not verified",
                    recommendation="Ensure medical forms are fully accessible with proper labels and error handling",
                    wcag_level=WCAGLevel.A,
                    impact="High",
                    page_url=page_url
                )
                self.healthcare_violations.append(violation)

    def _test_appointment_accessibility(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test appointment scheduling accessibility"""
        appointment_elements = soup.find_all(class_=lambda x: x and 'appointment' in x.lower())

        for element in appointment_elements:
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.OPERABLE_2_4_6,
                violation_type=AccessibilityViolationType.MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY,
                element=f"Appointment scheduling: {element.get_text()[:50]}...",
                element_selector=str(element.name),
                severity="Serious",
                description="Appointment scheduling accessibility not verified",
                recommendation="Ensure appointment scheduling is accessible",
                wcag_level=WCAGLevel.AA,
                impact="High",
                page_url=page_url
            )
            self.healthcare_violations.append(violation)

    def _test_lab_results_accessibility(self, soup: BeautifulSoup, page_url: str):
        """Test lab results accessibility"""
        lab_elements = soup.find_all(class_=lambda x: x and 'lab' in x.lower())

        for element in lab_elements:
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.PERCEIVABLE_1_3_1,
                violation_type=AccessibilityViolationType.MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY,
                element=f"Lab results: {element.get_text()[:50]}...",
                element_selector=str(element.name),
                severity="Serious",
                description="Lab results accessibility not verified",
                recommendation="Ensure lab results are presented accessibly",
                wcag_level=WCAGLevel.AA,
                impact="High",
                page_url=page_url
            )
            self.healthcare_violations.append(violation)

    def _test_billing_accessibility(self, soup: BeautifulSoup, page_url: str):
        """Test billing information accessibility"""
        billing_elements = soup.find_all(class_=lambda x: x and 'billing' in x.lower())

        for element in billing_elements:
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.OPERABLE_3_3_2,
                violation_type=AccessibilityViolationType.MISSING_HEALTHCARE_SPECIFIC_ACCESSIBILITY,
                element=f"Billing information: {element.get_text()[:50]}...",
                element_selector=str(element.name),
                severity="Serious",
                description="Billing information accessibility not verified",
                recommendation="Ensure billing information is accessible and understandable",
                wcag_level=WCAGLevel.AA,
                impact="High",
                page_url=page_url
            )
            self.healthcare_violations.append(violation)

    def _has_visible_focus(self, driver: WebDriver, element) -> bool:
        """Check if element has visible focus"""
        try:
            # Check for focus styles
            style = element.get_attribute('style') or ''
            return 'outline' in style or 'border' in style
        except:
            return False

    def _calculate_wcag_compliance(self) -> Dict[WCAGLevel, float]:
        """Calculate WCAG compliance percentage by level"""
        total_guidelines = len(WCAGGuideline)

        # Count violations by WCAG level
        level_violations = {
            WCAGLevel.A: len([v for v in self.violations if v.wcag_level == WCAGLevel.A]),
            WCAGLevel.AA: len([v for v in self.violations if v.wcag_level == WCAGLevel.AA]),
            WCAGLevel.AAA: len([v for v in self.violations if v.wcag_level == WCAGLevel.AAA])
        }

        # Calculate compliance percentages
        compliance = {}
        for level in WCAGLevel:
            violations = level_violations.get(level, 0)
            compliance_percentage = max(0, 100 - (violations / total_guidelines * 100))
            compliance[level] = round(compliance_percentage, 1)

        return compliance

    def _calculate_overall_score(self) -> float:
        """Calculate overall accessibility score"""
        if not self.violations:
            return 100.0

        # Weight violations by severity
        severity_weights = {
            'Critical': 10,
            'Serious': 5,
            'Moderate': 2,
            'Minor': 1
        }

        total_weight = sum(severity_weights.get(v.severity, 1) for v in self.violations)
        max_weight = len(self.violations) * 10  # Maximum possible weight

        score = max(0, 100 - (total_weight / max_weight * 100))
        return round(score, 1)

    def _generate_recommendations(self) -> List[str]:
        """Generate accessibility recommendations"""
        recommendations = []

        # Group violations by type
        violation_types = {}
        for violation in self.violations:
            vtype = violation.violation_type
            if vtype not in violation_types:
                violation_types[vtype] = []
            violation_types[vtype].append(violation)

        # Generate recommendations based on violation types
        if AccessibilityViolationType.MISSING_ALT_TEXT in violation_types:
            recommendations.append("Add descriptive alt text to all images and non-text content")

        if AccessibilityViolationType.LOW_CONTRAST in violation_types:
            recommendations.append("Improve color contrast ratios to meet WCAG 2.1 AA standards")

        if AccessibilityViolationType.MISSING_FORM_LABEL in violation_types:
            recommendations.append("Add proper labels to all form inputs using <label> or aria-label")

        if AccessibilityViolationType.MISSING_FOCUS_VISIBLE in violation_types:
            recommendations.append("Ensure focus is clearly visible on all interactive elements")

        if AccessibilityViolationType.MISSING_KEYBOARD_NAVIGATION in violation_types:
            recommendations.append("Improve keyboard navigation and remove keyboard traps")

        if AccessibilityViolationType.MISSING_LANDMARK in violation_types:
            recommendations.append("Add proper landmark regions (header, nav, main, footer)")

        if self.healthcare_violations:
            recommendations.append("Address healthcare-specific accessibility requirements")

        return recommendations

    def _test_adaptable_content(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test adaptable content (WCAG 1.3)"""
        self._test_heading_structure(soup, page_url)
        self._test_landmark_regions(soup, page_url)
        self._test_table_accessibility(soup, page_url)

    def _test_distinguishable_content(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test distinguishable content (WCAG 1.4)"""
        self._test_contrast_ratio(driver, soup, page_url)

        # Test responsive design
        try:
            # Test different viewport sizes
            driver.set_window_size(320, 568)  # Mobile
            driver.save_screenshot(f"/tmp/mobile_{hash(page_url)}.png")

            driver.set_window_size(768, 1024)  # Tablet
            driver.save_screenshot(f"/tmp/tablet_{hash(page_url)}.png")

            driver.set_window_size(1920, 1080)  # Desktop
            driver.save_screenshot(f"/tmp/desktop_{hash(page_url)}.png")

        except Exception as e:
            logger.warning(f"Responsive design test failed: {e}")

    def _test_timing_controls(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test timing controls (WCAG 2.2)"""
        # Check for time-based interactions
        timed_elements = soup.find_all(['video', 'audio', 'script'])

        for element in timed_elements:
            if element.name in ['video', 'audio']:
                # Check for controls
                if not element.get('controls'):
                    violation = AccessibilityTestResult(
                        guideline=WCAGGuideline.OPERABLE_2_2_2,
                        violation_type=AccessibilityViolationType.MISSING_AUDIO_DESCRIPTION,
                        element=f"Media element: {element.name}",
                        element_selector=str(element.name),
                        severity="Moderate",
                        description="Media element missing controls",
                        recommendation="Add controls to time-based media",
                        wcag_level=WCAGLevel.A,
                        impact="Medium",
                        page_url=page_url
                    )
                    self.violations.append(violation)

    def _test_seizure_controls(self, soup: BeautifulSoup, page_url: str):
        """Test seizure controls (WCAG 2.3)"""
        # Check for flashing content
        # This is a simplified test - in practice, you'd analyze animations
        pass

    def _test_navigation_structure(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test navigation structure (WCAG 2.4)"""
        self._test_page_title(soup, page_url)
        self._test_heading_structure(soup, page_url)
        self._test_landmark_regions(soup, page_url)

        # Test skip links
        skip_links = soup.find_all('a', href=lambda x: x and x.startswith('#'))
        if not skip_links:
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.OPERABLE_2_4_1,
                violation_type=AccessibilityViolationType.MISSING_SKIP_LINK,
                element="Skip navigation link",
                element_selector="body",
                severity="Moderate",
                description="Missing skip navigation link",
                recommendation="Add skip navigation link for keyboard users",
                wcag_level=WCAGLevel.A,
                impact="Medium",
                page_url=page_url
            )
            self.violations.append(violation)

    def _test_input_modalities(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test input modalities (WCAG 2.5)"""
        # Test pointer gestures and cancellation
        pass

    def _test_readable_content(self, soup: BeautifulSoup, page_url: str):
        """Test readable content (WCAG 3.1)"""
        self._test_language_attributes(soup, page_url)

    def _test_predictable_content(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test predictable content (WCAG 3.2)"""
        # Test consistent navigation and identification
        pass

    def _test_input_assistance(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test input assistance (WCAG 3.3)"""
        self._test_form_labels(soup, page_url)

        # Test error handling
        error_elements = soup.find_all(class_=lambda x: x and 'error' in x.lower())
        if not error_elements:
            violation = AccessibilityTestResult(
                guideline=WCAGGuideline.UNDERSTANDABLE_3_3_1,
                violation_type=AccessibilityViolationType.MISSING_ERROR_MESSAGE,
                element="Error handling",
                element_selector="form",
                severity="Serious",
                description="Missing error identification and handling",
                recommendation="Provide clear error messages and suggestions",
                wcag_level=WCAGLevel.A,
                impact="High",
                page_url=page_url
            )
            self.violations.append(violation)

    def _test_compatibility(self, driver: WebDriver, soup: BeautifulSoup, page_url: str):
        """Test compatibility (WCAG 4.1)"""
        # Test HTML validity and ARIA attributes
        pass

    def _test_time_based_media(self, soup: BeautifulSoup, page_url: str):
        """Test time-based media (WCAG 1.2)"""
        media_elements = soup.find_all(['video', 'audio'])

        for element in media_elements:
            if element.name == 'video':
                # Check for captions
                if not element.find('track', kind='captions'):
                    violation = AccessibilityTestResult(
                        guideline=WCAGGuideline.PERCEIVABLE_1_2_2,
                        violation_type=AccessibilityViolationType.MISSING_CAPTION,
                        element=f"Video: {element.get('src', 'unknown')}",
                        element_selector="video",
                        severity="Serious",
                        description="Video missing captions",
                        recommendation="Add captions to all video content",
                        wcag_level=WCAGLevel.A,
                        impact="High",
                        page_url=page_url
                    )
                    self.violations.append(violation)

    def generate_accessibility_report(self, audit_result: AccessibilityAuditResult) -> str:
        """Generate comprehensive accessibility report"""
        report = f"""
# Accessibility Audit Report
**URL:** {audit_result.page_url}
**Date:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(audit_result.timestamp))}
**Overall Score:** {audit_result.overall_score:.1f}%

## Summary
- **Total Violations:** {audit_result.total_violations}
- **Critical:** {audit_result.critical_violations}
- **Serious:** {audit_result.serious_violations}
- **Moderate:** {audit_result.moderate_violations}
- **Minor:** {audit_result.minor_violations}

## WCAG Compliance
- **Level A:** {audit_result.wcag_compliance.get(WCAGLevel.A, 0):.1f}%
- **Level AA:** {audit_result.wcag_compliance.get(WCAGLevel.AA, 0):.1f}%
- **Level AAA:** {audit_result.wcag_compliance.get(WCAGLevel.AAA, 0):.1f}%

## Healthcare-Specific Issues
- **Total Issues:** {len(audit_result.healthcare_specific_issues)}

## Key Recommendations
"""

        for i, rec in enumerate(audit_result.recommendations[:10], 1):
            report += f"{i}. {rec}\n"

        report += "\n## Detailed Violations\n"

        # Group violations by severity
        by_severity = {}
        for violation in audit_result.violations:
            if violation.severity not in by_severity:
                by_severity[violation.severity] = []
            by_severity[violation.severity].append(violation)

        for severity in ['Critical', 'Serious', 'Moderate', 'Minor']:
            if severity in by_severity:
                report += f"\n### {severity} Violations\n"
                for violation in by_severity[severity][:5]:  # Limit to top 5 per severity
                    report += f"- **{violation.violation_type.value}**: {violation.description}\n"
                    report += f"  - Element: {violation.element}\n"
                    report += f"  - WCAG: {violation.guideline.value} ({violation.wcag_level.value})\n"
                    report += f"  - Recommendation: {violation.recommendation}\n"

        return report

# Pytest fixtures and helpers
@pytest.fixture
def accessibility_framework():
    """Accessibility testing framework fixture"""
    return AccessibilityTestingFramework()

@pytest.fixture
def chrome_driver():
    """Chrome WebDriver fixture for accessibility testing"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    yield driver
    driver.quit()

@pytest.fixture
def mobile_driver():
    """Mobile WebDriver fixture for accessibility testing"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=375,667')  # iPhone 8

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    yield driver
    driver.quit()

# Test classes
class AccessibilityTestMixin:
    """Mixin class for accessibility testing"""

    def assert_accessibility_compliance(self, audit_result: AccessibilityAuditResult, min_score: float = 80.0):
        """Assert that accessibility score meets minimum requirement"""
        assert audit_result.overall_score >= min_score, \
            f"Accessibility score {audit_result.overall_score:.1f}% is below minimum {min_score}%"

    def assert_no_critical_violations(self, audit_result: AccessibilityAuditResult):
        """Assert that there are no critical accessibility violations"""
        assert audit_result.critical_violations == 0, \
            f"Found {audit_result.critical_violations} critical accessibility violations"

    def assert_wcag_aa_compliance(self, audit_result: AccessibilityAuditResult, min_compliance: float = 90.0):
        """Assert WCAG AA compliance meets minimum requirement"""
        aa_compliance = audit_result.wcag_compliance.get(WCAGLevel.AA, 0)
        assert aa_compliance >= min_compliance, \
            f"WCAG AA compliance {aa_compliance:.1f}% is below minimum {min_compliance}%"

class HealthcareAccessibilityTestMixin(AccessibilityTestMixin):
    """Healthcare-specific accessibility testing mixin"""

    def assert_healthcare_accessibility_compliance(self, audit_result: AccessibilityAuditResult):
        """Assert healthcare-specific accessibility compliance"""
        assert len(audit_result.healthcare_specific_issues) <= 5, \
            f"Found {len(audit_result.healthcare_specific_issues)} healthcare accessibility issues"

    def assert_emergency_information_accessibility(self, audit_result: AccessibilityAuditResult):
        """Assert emergency information is accessible"""
        emergency_violations = [
            v for v in audit_result.healthcare_specific_issues
            if 'emergency' in v.element.lower()
        ]
        assert len(emergency_violations) == 0, \
            f"Found {len(emergency_violations)} emergency information accessibility issues"

def run_accessibility_audit(url: str, driver: Optional[WebDriver] = None) -> AccessibilityAuditResult:
    """Run accessibility audit on given URL"""
    framework = AccessibilityTestingFramework()
    return framework.run_comprehensive_accessibility_audit(url, driver)