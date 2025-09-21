#!/usr/bin/env python3
"""
Comprehensive Test Runner for Enterprise-Grade HMS

This script provides a unified interface for running all types of tests
in the Healthcare Management System testing framework.
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestRunner:
    """Comprehensive test runner for HMS testing framework"""

    def __init__(self):
        self.project_root = project_root
        self.test_dir = project_root / 'tests'
        self.results_dir = project_root / 'test_results'
        self.results_dir.mkdir(exist_ok=True)

        # Test categories with their configurations
        self.test_categories = {
            'unit': {
                'description': 'Unit tests for models, views, serializers',
                'command': ['pytest', 'tests/unit/', '-m', 'unit', '--cov=.'],
                'timeout': 300,
                'required': True
            },
            'integration': {
                'description': 'Integration tests for API endpoints',
                'command': ['pytest', 'tests/integration/', '-m', 'integration'],
                'timeout': 600,
                'required': True
            },
            'e2e': {
                'description': 'End-to-end tests for user journeys',
                'command': ['pytest', 'tests/e2e/', '-m', 'e2e'],
                'timeout': 1200,
                'required': True
            },
            'performance': {
                'description': 'Performance and load testing',
                'command': ['pytest', 'tests/performance/', '-m', 'performance'],
                'timeout': 1800,
                'required': False
            },
            'security': {
                'description': 'Security testing and vulnerability assessment',
                'command': ['pytest', 'tests/security/', '-m', 'security'],
                'timeout': 900,
                'required': True
            },
            'compliance': {
                'description': 'Healthcare compliance testing (HIPAA, GDPR, etc.)',
                'command': ['pytest', 'tests/compliance/', '-m', 'compliance'],
                'timeout': 1200,
                'required': True
            },
            'accessibility': {
                'description': 'Accessibility testing (WCAG 2.1)',
                'command': ['pytest', 'tests/accessibility/', '-m', 'accessibility'],
                'timeout': 600,
                'required': True
            },
            'cross_browser': {
                'description': 'Cross-browser and mobile testing',
                'command': ['pytest', 'tests/cross_browser/', '-m', 'cross_browser'],
                'timeout': 1800,
                'required': False
            },
            'database': {
                'description': 'Database migration and integrity testing',
                'command': ['pytest', 'tests/database_migration/', '-m', 'database'],
                'timeout': 900,
                'required': True
            }
        }

    def run_test_category(self, category: str, verbose: bool = False) -> Dict[str, Any]:
        """Run tests for a specific category"""
        if category not in self.test_categories:
            raise ValueError(f"Unknown test category: {category}")

        config = self.test_categories[category]
        logger.info(f"Running {category} tests: {config['description']}")

        start_time = time.time()
        result = {
            'category': category,
            'description': config['description'],
            'start_time': start_time,
            'status': 'running',
            'output': '',
            'exit_code': None,
            'duration': 0
        }

        try:
            # Set environment variables
            env = os.environ.copy()
            env.update({
                'TEST_CATEGORY': category,
                'TEST_VERBOSE': str(verbose).lower(),
                'PYTHONPATH': str(self.project_root)
            })

            # Run the test command
            process = subprocess.Popen(
                config['command'],
                cwd=self.project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Capture output with timeout
            try:
                stdout, _ = process.communicate(timeout=config['timeout'])
                result['output'] = stdout
                result['exit_code'] = process.returncode
                result['status'] = 'passed' if process.returncode == 0 else 'failed'
            except subprocess.TimeoutExpired:
                process.kill()
                result['output'] = f"Test timed out after {config['timeout']} seconds"
                result['status'] = 'timeout'
                result['exit_code'] = -1

            result['duration'] = time.time() - start_time

        except Exception as e:
            result['status'] = 'error'
            result['output'] = str(e)
            result['duration'] = time.time() - start_time
            logger.error(f"Error running {category} tests: {e}")

        # Save result to file
        result_file = self.results_dir / f"{category}_result.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)

        return result

    def run_all_tests(self, categories: Optional[List[str]] = None,
                     verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
        """Run all tests or specified categories"""
        if categories is None:
            categories = list(self.test_categories.keys())

        logger.info(f"Running test categories: {categories}")

        results = {
            'start_time': time.time(),
            'categories': categories,
            'results': {},
            'summary': {
                'total': len(categories),
                'passed': 0,
                'failed': 0,
                'timeout': 0,
                'error': 0
            }
        }

        # Run tests (sequentially for now, could be extended for parallel)
        for category in categories:
            result = self.run_test_category(category, verbose)
            results['results'][category] = result

            # Update summary
            if result['status'] in results['summary']:
                results['summary'][result['status']] += 1

        results['end_time'] = time.time()
        results['total_duration'] = results['end_time'] - results['start_time']

        # Save comprehensive results
        results_file = self.results_dir / 'comprehensive_test_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        return results

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Execution Time: {results['total_duration']:.2f} seconds")
        report.append(f"Total Categories: {results['summary']['total']}")
        report.append("")

        # Summary
        report.append("SUMMARY:")
        report.append(f"  Passed: {results['summary']['passed']}")
        report.append(f"  Failed: {results['summary']['failed']}")
        report.append(f"  Timeout: {results['summary']['timeout']}")
        report.append(f"  Error: {results['summary']['error']}")
        report.append("")

        # Category details
        report.append("CATEGORY RESULTS:")
        report.append("-" * 40)
        for category, result in results['results'].items():
            status_symbol = {
                'passed': '✓',
                'failed': '✗',
                'timeout': '⏱',
                'error': '!'
            }.get(result['status'], '?')

            report.append(f"{status_symbol} {category.upper()}")
            report.append(f"    Status: {result['status']}")
            report.append(f"    Duration: {result['duration']:.2f}s")
            report.append(f"    Description: {result['description']}")
            if result['exit_code'] is not None:
                report.append(f"    Exit Code: {result['exit_code']}")
            report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 40)

        if results['summary']['failed'] > 0:
            report.append("• Review failed test categories and fix issues")
            report.append("• Check test output for specific error details")

        if results['summary']['timeout'] > 0:
            report.append("• Investigate timeout issues and optimize test performance")
            report.append("• Consider increasing timeout values if necessary")

        if results['summary']['error'] > 0:
            report.append("• Fix environment and configuration issues")
            report.append("• Check test dependencies and requirements")

        if results['summary']['passed'] == results['summary']['total']:
            report.append("• All tests passed! System is ready for deployment")

        report.append("")
        report.append("DETAILED RESULTS:")
        report.append(f"  Results saved to: {self.results_dir}")
        report.append(f"  Coverage report: {self.project_root}/htmlcov/")
        report.append(f"  Execution log: test_execution.log")

        return "\n".join(report)

    def setup_environment(self) -> bool:
        """Setup test environment"""
        logger.info("Setting up test environment...")

        try:
            # Create necessary directories
            directories = [
                self.results_dir,
                self.project_root / 'htmlcov',
                self.project_root / 'test_data'
            ]

            for directory in directories:
                directory.mkdir(exist_ok=True)

            # Set environment variables
            os.environ.update({
                'DJANGO_SETTINGS_MODULE': 'backend.hms.settings_test',
                'TEST_ENVIRONMENT': 'test',
                'TEST_MODE': 'true',
                'PYTHONPATH': str(self.project_root)
            })

            logger.info("Test environment setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False

    def cleanup(self) -> None:
        """Cleanup after test execution"""
        logger.info("Cleaning up test environment...")

        # Additional cleanup tasks can be added here
        # For example: cleanup test data, close connections, etc.

        logger.info("Cleanup completed")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Runner for Enterprise-Grade HMS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                          # Run all test categories
  %(prog)s --categories unit integration   # Run specific categories
  %(prog)s --security --verbose           # Run security tests with verbose output
  %(prog)s --compliance --report           # Run compliance tests and generate report
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all test categories'
    )

    parser.add_argument(
        '--categories',
        nargs='+',
        choices=list(TestRunner().test_categories.keys()),
        help='Specific test categories to run'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run tests in parallel (if supported)'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate comprehensive test report'
    )

    parser.add_argument(
        '--setup-only',
        action='store_true',
        help='Only setup the test environment'
    )

    parser.add_argument(
        '--list-categories',
        action='store_true',
        help='List available test categories'
    )

    args = parser.parse_args()

    # Initialize test runner
    runner = TestRunner()

    # List categories if requested
    if args.list_categories:
        print("Available test categories:")
        for category, config in runner.test_categories.items():
            print(f"  {category}: {config['description']}")
        return 0

    # Setup only if requested
    if args.setup_only:
        success = runner.setup_environment()
        return 0 if success else 1

    # Determine categories to run
    if args.all:
        categories = None  # Run all categories
    elif args.categories:
        categories = args.categories
    else:
        print("No test categories specified. Use --all or --categories.")
        print("Use --list-categories to see available options.")
        return 1

    # Setup environment
    if not runner.setup_environment():
        return 1

    try:
        # Run tests
        results = runner.run_all_tests(categories, args.verbose, args.parallel)

        # Generate report if requested
        if args.report:
            report = runner.generate_report(results)
            print(report)

            # Save report to file
            report_file = runner.results_dir / 'test_report.txt'
            with open(report_file, 'w') as f:
                f.write(report)

        # Return appropriate exit code
        if results['summary']['failed'] > 0 or results['summary']['error'] > 0:
            return 1
        else:
            return 0

    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        runner.cleanup()

if __name__ == '__main__':
    sys.exit(main())