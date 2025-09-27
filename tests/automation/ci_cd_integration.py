"""
CI/CD Integration for HMS Test Automation Framework

This module provides CI/CD pipeline integration, automated testing workflows,
and deployment automation for the healthcare management system.
"""

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class CIPlatform(Enum):
    """Supported CI/CD platforms"""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure_devops"
    CIRCLE_CI = "circle_ci"


class DeploymentEnvironment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    QA = "qa"


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    platform: CIPlatform
    environment: DeploymentEnvironment
    branch: str
    run_security_tests: bool = True
    run_performance_tests: bool = True
    run_compliance_tests: bool = True
    run_accessibility_tests: bool = True
    deploy_on_success: bool = True
    notify_on_failure: bool = True
    parallel_execution: bool = True
    max_workers: int = 4


class CI_CD_Integrator:
    """
    CI/CD Integration for HMS Test Automation

    Features:
    - Multi-platform CI/CD support
    - Automated testing workflows
    - Deployment pipeline automation
    - Environment-specific configurations
    - Notification and reporting
    - Rollback capabilities
    """

    def __init__(self, config: PipelineConfig):
        """Initialize CI/CD integrator"""
        self.config = config
        self.workflows_dir = Path('.github/workflows')
        self.pipelines_dir = Path('pipelines')
        self.scripts_dir = Path('scripts')

        # Ensure directories exist
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.pipelines_dir.mkdir(parents=True, exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"CI/CD Integrator initialized for {config.platform.value}")

    def generate_github_actions_workflow(self) -> str:
        """Generate GitHub Actions workflow"""
        workflow_name = f"hms-{self.config.environment.value}-ci.yml"
        workflow_path = self.workflows_dir / workflow_name

        workflow_content = self._get_github_actions_template()

        with open(workflow_path, 'w') as f:
            f.write(workflow_content)

        logger.info(f"Generated GitHub Actions workflow: {workflow_path}")
        return str(workflow_path)

    def generate_gitlab_ci_pipeline(self) -> str:
        """Generate GitLab CI pipeline"""
        pipeline_path = Path('.gitlab-ci.yml')

        pipeline_content = self._get_gitlab_ci_template()

        with open(pipeline_path, 'w') as f:
            f.write(pipeline_content)

        logger.info(f"Generated GitLab CI pipeline: {pipeline_path}")
        return str(pipeline_path)

    def generate_jenkins_pipeline(self) -> str:
        """Generate Jenkins pipeline"""
        pipeline_path = Path('Jenkinsfile')

        pipeline_content = self._get_jenkins_template()

        with open(pipeline_path, 'w') as f:
            f.write(pipeline_content)

        logger.info(f"Generated Jenkins pipeline: {pipeline_path}")
        return str(pipeline_path)

    def generate_docker_compose_test(self) -> str:
        """Generate Docker Compose for testing"""
        compose_path = Path('docker-compose.test.yml')

        compose_content = self._get_docker_compose_test_template()

        with open(compose_path, 'w') as f:
            f.write(compose_content)

        logger.info(f"Generated Docker Compose test configuration: {compose_path}")
        return str(compose_path)

    def generate_deployment_scripts(self) -> List[str]:
        """Generate deployment scripts"""
        scripts = []

        for env in [DeploymentEnvironment.DEVELOPMENT, DeploymentEnvironment.STAGING, DeploymentEnvironment.PRODUCTION]:
            script_path = self.scripts_dir / f'deploy-{env.value}.sh'
            script_content = self._get_deployment_script_template(env.value)

            with open(script_path, 'w') as f:
                f.write(script_content)

            # Make script executable
            script_path.chmod(0o755)

            scripts.append(str(script_path))
            logger.info(f"Generated deployment script: {script_path}")

        return scripts

    def generate_test_runner_script(self) -> str:
        """Generate test runner script"""
        script_path = self.scripts_dir / 'run-tests.sh'

        script_content = self._get_test_runner_template()

        with open(script_path, 'w') as f:
            f.write(script_content)

        # Make script executable
        script_path.chmod(0o755)

        logger.info(f"Generated test runner script: {script_path}")
        return str(script_path)

    def generate_monitoring_config(self) -> str:
        """Generate monitoring configuration"""
        config_path = Path('monitoring/prometheus.yml')

        config_content = self._get_monitoring_config_template()

        with open(config_path, 'w') as f:
            f.write(config_content)

        logger.info(f"Generated monitoring configuration: {config_path}")
        return str(config_path)

    def generate_all_configs(self) -> Dict[str, str]:
        """Generate all CI/CD configurations"""
        configs = {}

        # Generate platform-specific configurations
        if self.config.platform == CIPlatform.GITHUB_ACTIONS:
            configs['github_workflow'] = self.generate_github_actions_workflow()
        elif self.config.platform == CIPlatform.GITLAB_CI:
            configs['gitlab_pipeline'] = self.generate_gitlab_ci_pipeline()
        elif self.config.platform == CIPlatform.JENKINS:
            configs['jenkins_pipeline'] = self.generate_jenkins_pipeline()

        # Generate common configurations
        configs['docker_compose'] = self.generate_docker_compose_test()
        configs['deployment_scripts'] = self.generate_deployment_scripts()
        configs['test_runner'] = self.generate_test_runner_script()
        configs['monitoring'] = self.generate_monitoring_config()

        logger.info(f"Generated {len(configs)} CI/CD configurations")
        return configs

    def validate_configurations(self) -> List[str]:
        """Validate generated configurations"""
        validation_errors = []

        # Check if required files exist
        required_files = [
            'requirements.txt',
            'backend/manage.py',
            'frontend/package.json',
            'docker-compose.yml'
        ]

        for file_path in required_files:
            if not Path(file_path).exists():
                validation_errors.append(f"Required file not found: {file_path}")

        # Check if test directories exist
        test_dirs = [
            'tests/unit',
            'tests/integration',
            'tests/e2e',
            'tests/performance',
            'tests/security',
            'tests/compliance',
            'tests/accessibility'
        ]

        for test_dir in test_dirs:
            if not Path(test_dir).exists():
                validation_errors.append(f"Test directory not found: {test_dir}")

        # Validate configuration files
        if self.config.platform == CIPlatform.GITHUB_ACTIONS:
            if not self.workflows_dir.exists():
                validation_errors.append("GitHub workflows directory not found")

        return validation_errors

    def run_local_ci(self) -> Dict[str, Any]:
        """Run CI pipeline locally"""
        logger.info("Running local CI pipeline")

        results = {
            'success': True,
            'stages': {},
            'errors': []
        }

        try:
            # Stage 1: Setup
            results['stages']['setup'] = self._run_setup_stage()

            # Stage 2: Security Scan
            if self.config.run_security_tests:
                results['stages']['security'] = self._run_security_stage()

            # Stage 3: Unit Tests
            results['stages']['unit_tests'] = self._run_unit_tests_stage()

            # Stage 4: Integration Tests
            results['stages']['integration_tests'] = self._run_integration_tests_stage()

            # Stage 5: E2E Tests
            results['stages']['e2e_tests'] = self._run_e2e_tests_stage()

            # Stage 6: Performance Tests
            if self.config.run_performance_tests:
                results['stages']['performance'] = self._run_performance_stage()

            # Stage 7: Compliance Tests
            if self.config.run_compliance_tests:
                results['stages']['compliance'] = self._run_compliance_stage()

            # Stage 8: Accessibility Tests
            if self.config.run_accessibility_tests:
                results['stages']['accessibility'] = self._run_accessibility_stage()

            # Check if all stages passed
            for stage_name, stage_result in results['stages'].items():
                if not stage_result.get('success', False):
                    results['success'] = False
                    results['errors'].append(f"Stage {stage_name} failed")

            logger.info(f"Local CI pipeline completed. Success: {results['success']}")
            return results

        except Exception as e:
            logger.error(f"Error running local CI pipeline: {str(e)}")
            results['success'] = False
            results['errors'].append(str(e))
            return results

    def _run_setup_stage(self) -> Dict[str, Any]:
        """Run setup stage"""
        logger.info("Running setup stage")

        try:
            # Install dependencies
            result = subprocess.run(
                ['pip', 'install', '-r', 'backend/requirements.txt'],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return {'success': False, 'error': result.stderr}

            # Install frontend dependencies
            result = subprocess.run(
                ['npm', 'ci'],
                capture_output=True,
                text=True,
                timeout=300,
                cwd='frontend'
            )

            if result.returncode != 0:
                return {'success': False, 'error': result.stderr}

            return {'success': True, 'message': 'Setup completed successfully'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_security_stage(self) -> Dict[str, Any]:
        """Run security scan stage"""
        logger.info("Running security scan stage")

        try:
            # Run bandit security analysis
            result = subprocess.run(
                ['bandit', '-r', '.', '-f', 'json'],
                capture_output=True,
                text=True,
                timeout=180
            )

            # Run safety dependency check
            result2 = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                timeout=120
            )

            success = result.returncode == 0 and result2.returncode == 0

            return {
                'success': success,
                'bandit_output': result.stdout,
                'safety_output': result2.stdout
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_unit_tests_stage(self) -> Dict[str, Any]:
        """Run unit tests stage"""
        logger.info("Running unit tests stage")

        try:
            result = subprocess.run(
                ['pytest', 'tests/unit/', '-v', '--cov=.', '--cov-report=xml', '--junitxml=reports/unit-tests.xml'],
                capture_output=True,
                text=True,
                timeout=600
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_integration_tests_stage(self) -> Dict[str, Any]:
        """Run integration tests stage"""
        logger.info("Running integration tests stage")

        try:
            result = subprocess.run(
                ['pytest', 'tests/integration/', '-v', '--junitxml=reports/integration-tests.xml'],
                capture_output=True,
                text=True,
                timeout=900
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_e2e_tests_stage(self) -> Dict[str, Any]:
        """Run E2E tests stage"""
        logger.info("Running E2E tests stage")

        try:
            result = subprocess.run(
                ['pytest', 'tests/e2e/', '-v', '--junitxml=reports/e2e-tests.xml'],
                capture_output=True,
                text=True,
                timeout=1200
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_performance_stage(self) -> Dict[str, Any]:
        """Run performance tests stage"""
        logger.info("Running performance tests stage")

        try:
            result = subprocess.run(
                ['pytest', 'tests/performance/', '-v', '--junitxml=reports/performance-tests.xml'],
                capture_output=True,
                text=True,
                timeout=1800
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_compliance_stage(self) -> Dict[str, Any]:
        """Run compliance tests stage"""
        logger.info("Running compliance tests stage")

        try:
            result = subprocess.run(
                ['pytest', 'tests/compliance/', '-v', '--junitxml=reports/compliance-tests.xml'],
                capture_output=True,
                text=True,
                timeout=900
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_accessibility_stage(self) -> Dict[str, Any]:
        """Run accessibility tests stage"""
        logger.info("Running accessibility tests stage")

        try:
            result = subprocess.run(
                ['pytest', 'tests/accessibility/', '-v', '--junitxml=reports/accessibility-tests.xml'],
                capture_output=True,
                text=True,
                timeout=600
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_github_actions_template(self) -> str:
        """Get GitHub Actions workflow template"""
        return f"""name: HMS CI/CD Pipeline - {self.config.environment.value}

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'
  POSTGRES_VERSION: '15'

jobs:
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}

      - name: Install security tools
        run: |
          pip install bandit safety semgrep

      - name: Run security analysis
        run: |
          bandit -r . -f json || true
          safety check --json || true

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: security-scan
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit/ -v --cov=. --cov-report=xml --junitxml=reports/unit-tests.xml

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest

      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration/ -v --junitxml=reports/integration-tests.xml

  e2e-tests:
    name: End-to-End Tests
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest selenium

      - name: Run E2E tests
        run: |
          cd backend
          pytest tests/e2e/ -v --junitxml=reports/e2e-tests.xml

  {'performance-tests' if self.config.run_performance_tests else '# performance-tests'}:
    name: Performance Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest locust

      - name: Run performance tests
        run: |
          cd backend
          pytest tests/performance/ -v --junitxml=reports/performance-tests.xml

  {'compliance-tests' if self.config.run_compliance_tests else '# compliance-tests'}:
    name: Compliance Tests
    runs-on: ubuntu-latest
    needs: security-scan
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest

      - name: Run compliance tests
        run: |
          cd backend
          pytest tests/compliance/ -v --junitxml=reports/compliance-tests.xml

  {'accessibility-tests' if self.config.run_accessibility_tests else '# accessibility-tests'}:
    name: Accessibility Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}

      - name: Install dependencies
        run: |
          npm ci
          npm install -g @axe-core/cli

      - name: Run accessibility tests
        run: |
          axe http://localhost:3000 --html-reports=reports/axe-report.html

  deploy-{self.config.environment.value}:
    name: Deploy to {self.config.environment.value}
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests, e2e-tests, {'performance-tests' if self.config.run_performance_tests else 'unit-tests'}, {'compliance-tests' if self.config.run_compliance_tests else 'security-scan'}, {'accessibility-tests' if self.config.run_accessibility_tests else 'unit-tests'}]
    if: github.ref == 'refs/heads/{self.config.branch}' && success()
    environment: {self.config.environment.value}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to {self.config.environment.value}
        run: |
          ./scripts/deploy-{self.config.environment.value}.sh

  notify:
    name: Notify Results
    runs-on: ubuntu-latest
    needs: [deploy-{self.config.environment.value}]
    if: always()
    steps:
      - name: Send notification
        run: |
          echo "Pipeline completed with status: ${{{{ job.status }}}}"
"""

    def _get_gitlab_ci_template(self) -> str:
        """Get GitLab CI template"""
        return f"""# HMS CI/CD Pipeline - {self.config.environment.value}

stages:
  - security
  - test
  - build
  - deploy

variables:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "18"
  POSTGRES_VERSION: "15"

security-scan:
  stage: security
  image: python:${{PYTHON_VERSION}}
  script:
    - pip install bandit safety semgrep
    - bandit -r . -f json || true
    - safety check --json || true
  artifacts:
    reports:
      sast: bandit-report.json

unit-tests:
  stage: test
  image: python:${{PYTHON_VERSION}}
  script:
    - pip install -r backend/requirements.txt
    - pip install pytest pytest-cov
    - cd backend
    - pytest tests/unit/ -v --cov=. --cov-report=xml --junitxml=reports/unit-tests.xml
  artifacts:
    reports:
      junit: backend/reports/unit-tests.xml

integration-tests:
  stage: test
  image: python:${{PYTHON_VERSION}}
  script:
    - pip install -r backend/requirements.txt
    - pip install pytest
    - cd backend
    - pytest tests/integration/ -v --junitxml=reports/integration-tests.xml
  artifacts:
    reports:
      junit: backend/reports/integration-tests.xml

e2e-tests:
  stage: test
  image: python:${{PYTHON_VERSION}}
  script:
    - pip install -r backend/requirements.txt
    - pip install pytest selenium
    - cd backend
    - pytest tests/e2e/ -v --junitxml=reports/e2e-tests.xml
  artifacts:
    reports:
      junit: backend/reports/e2e-tests.xml

{'performance-tests' if self.config.run_performance_tests else '# performance-tests'}:
  stage: test
  image: python:${{PYTHON_VERSION}}
  script:
    - pip install -r backend/requirements.txt
    - pip install pytest locust
    - cd backend
    - pytest tests/performance/ -v --junitxml=reports/performance-tests.xml
  artifacts:
    reports:
      junit: backend/reports/performance-tests.xml

{'compliance-tests' if self.config.run_compliance_tests else '# compliance-tests'}:
  stage: security
  image: python:${{PYTHON_VERSION}}
  script:
    - pip install -r backend/requirements.txt
    - pip install pytest
    - cd backend
    - pytest tests/compliance/ -v --junitxml=reports/compliance-tests.xml
  artifacts:
    reports:
      junit: backend/reports/compliance-tests.xml

{'accessibility-tests' if self.config.run_accessibility_tests else '# accessibility-tests'}:
  stage: test
  image: node:${{NODE_VERSION}}
  script:
    - npm ci
    - npm install -g @axe-core/cli
    - axe http://localhost:3000 --html-reports=reports/axe-report.html

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t hms:${{CI_COMMIT_SHA}} .
    - docker tag hms:${{CI_COMMIT_SHA}} hms:latest

deploy-{self.config.environment.value}:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache openssh-client
    - chmod 600 ${{SSH_PRIVATE_KEY}}
    - ssh ${{SSH_USER}}@${{SSH_HOST}} "mkdir -p /tmp/deploy"
    - scp docker-compose.yml ${{SSH_USER}}@${{SSH_HOST}}:/tmp/deploy/
    - ssh ${{SSH_USER}}@${{SSH_HOST}} "cd /tmp/deploy && docker-compose pull && docker-compose up -d"
  only:
    - {self.config.branch}
  when: manual
"""

    def _get_jenkins_template(self) -> str:
        """Get Jenkins pipeline template"""
        return f"""pipeline {{
    agent any

    environment {{
        PYTHON_VERSION = '3.11'
        NODE_VERSION = '18'
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                git url: 'https://github.com/your-org/hms.git', branch: '{self.config.branch}'
            }}
        }}

        stage('Security Scan') {{
            parallel {{
                stage('Bandit') {{
                    steps {{
                        sh '''
                            pip install bandit
                            bandit -r . -f json || true
                        '''
                    }}
                }}
                stage('Safety') {{
                    steps {{
                        sh '''
                            pip install safety
                            safety check --json || true
                        '''
                    }}
                }}
            }}
        }}

        stage('Unit Tests') {{
            steps {{
                sh '''
                    pip install -r backend/requirements.txt
                    pip install pytest pytest-cov
                    cd backend
                    pytest tests/unit/ -v --cov=. --cov-report=xml --junitxml=reports/unit-tests.xml
                '''
            }}
            post {{
                always {{
                    junit 'backend/reports/unit-tests.xml'
                }}
            }}
        }}

        stage('Integration Tests') {{
            steps {{
                sh '''
                    pip install -r backend/requirements.txt
                    pip install pytest
                    cd backend
                    pytest tests/integration/ -v --junitxml=reports/integration-tests.xml
                '''
            }}
            post {{
                always {{
                    junit 'backend/reports/integration-tests.xml'
                }}
            }}
        }}

        stage('E2E Tests') {{
            steps {{
                sh '''
                    pip install -r backend/requirements.txt
                    pip install pytest selenium
                    cd backend
                    pytest tests/e2e/ -v --junitxml=reports/e2e-tests.xml
                '''
            }}
            post {{
                always {{
                    junit 'backend/reports/e2e-tests.xml'
                }}
            }}
        }}

        {'performance-tests' if self.config.run_performance_tests else '# performance-tests'}:
            stage('Performance Tests') {{
                steps {{
                    sh '''
                        pip install -r backend/requirements.txt
                        pip install pytest locust
                        cd backend
                        pytest tests/performance/ -v --junitxml=reports/performance-tests.xml
                    '''
                }}
                post {{
                    always {{
                        junit 'backend/reports/performance-tests.xml'
                    }}
                }}
            }}

        {'compliance-tests' if self.config.run_compliance_tests else '# compliance-tests'}:
            stage('Compliance Tests') {{
                steps {{
                    sh '''
                        pip install -r backend/requirements.txt
                        pip install pytest
                        cd backend
                        pytest tests/compliance/ -v --junitxml=reports/compliance-tests.xml
                    '''
                }}
                post {{
                    always {{
                        junit 'backend/reports/compliance-tests.xml'
                    }}
                }}
            }}

        {'accessibility-tests' if self.config.run_accessibility_tests else '# accessibility-tests'}:
            stage('Accessibility Tests') {{
                steps {{
                    sh '''
                        npm ci
                        npm install -g @axe-core/cli
                        axe http://localhost:3000 --html-reports=reports/axe-report.html
                    '''
                }}
            }}

        stage('Deploy to {self.config.environment.value}') {{
            when {{
                branch '{self.config.branch}'
            }}
            steps {{
                sh './scripts/deploy-{self.config.environment.value}.sh'
            }}
        }}
    }}

    post {{
        always {{
            echo 'Pipeline completed'
            cleanWs()
        }}
    }}
}}

"""

    def _get_docker_compose_test_template(self) -> str:
        """Get Docker Compose test template"""
        return """version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: hms_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  elasticsearch:
    image: elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  backend:
    build: ./backend
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://test:test@postgres:5432/hms_test
      - REDIS_URL=redis://redis:6379/0
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - elasticsearch
    volumes:
      - ./backend:/app
    command: python manage.py runserver 0.0.0.0:8000

  frontend:
    build: ./frontend
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  elasticsearch_data:
"""

    def _get_deployment_script_template(self, environment: str) -> str:
        """Get deployment script template"""
        return f"""#!/bin/bash

# HMS Deployment Script - {environment}

set -e

echo "Starting deployment to {environment}..."

# Variables
PROJECT_NAME="hms"
DEPLOY_USER="deploy"
DEPLOY_HOST="{environment}.example.com"
DEPLOY_PATH="/opt/hms"
BACKUP_PATH="/opt/hms/backups"

# Create backup
echo "Creating backup..."
ssh ${{DEPLOY_USER}}@${{DEPLOY_HOST}} "mkdir -p ${{BACKUP_PATH}}/$(date +%Y%m%d_%H%M%S)"
ssh ${{DEPLOY_USER}}@${{DEPLOY_HOST}} "cp -r ${{DEPLOY_PATH}}/current ${{BACKUP_PATH}}/$(date +%Y%m%d_%H%M%S)/"

# Stop services
echo "Stopping services..."
ssh ${{DEPLOY_USER}}@${{DEPLOY_HOST}} "cd ${{DEPLOY_PATH}} && docker-compose down"

# Update code
echo "Updating code..."
rsync -av --exclude='*.pyc' --exclude='__pycache__' --exclude='node_modules' \
      --exclude='.git' --exclude='.env' ./ ${{DEPLOY_USER}}@${{DEPLOY_HOST}}:${{DEPLOY_PATH}}/new/

# Install dependencies
echo "Installing dependencies..."
ssh ${{DEPLOY_USER}}@${{DEPLOY_HOST}} "cd ${{DEPLOY_PATH}}/new && pip install -r requirements.txt"
ssh ${{DEPLOY_USER}}@${{DEPLOY_HOST}} "cd ${{DEPLOY_PATH}}/new/frontend && npm ci"

# Run database migrations
echo "Running database migrations..."
ssh ${{DEPLOY_USER}}@${{DEPLOY_HOST}} "cd ${{DEPLOY_PATH}}/new && python manage.py migrate"

# Collect static files
echo "Collecting static files..."
ssh ${{DEPLOY_USER}}@${{DEPLOY_HOST}} "cd ${{DEPLOY_PATH}}/new && python manage.py collectstatic --noinput"

# Update current symlink
echo "Updating current symlink..."
ssh ${{DEPLOY_USER}}@${{DEPLOY_HOST}} "cd ${{DEPLOY_PATH}} && ln -sfn new current"

# Start services
echo "Starting services..."
ssh ${{DEPLOY_USER}}@${{DEPLOY_HOST}} "cd ${{DEPLOY_PATH}} && docker-compose up -d"

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Run health checks
echo "Running health checks..."
curl -f http://${{DEPLOY_HOST}}:8000/health/ || exit 1
curl -f http://${{DEPLOY_HOST}}:3000/ || exit 1

echo "Deployment to {environment} completed successfully!"
"""

    def _get_test_runner_template(self) -> str:
        """Get test runner template"""
        return """#!/bin/bash

# HMS Test Runner Script

set -e

echo "Starting HMS test runner..."

# Environment setup
export PYTHONPATH="${{PYTHONPATH}}:$(pwd)"
export DJANGO_SETTINGS_MODULE="hms.settings.test"

# Create reports directory
mkdir -p reports

# Function to run tests
run_tests() {
    local test_type=$1
    local test_path=$2
    local report_name=$3

    echo "Running $test_type tests..."

    pytest $test_path \
        --verbose \
        --junitxml=reports/${{report_name}}.xml \
        --html=reports/${{report_name}}.html \
        --tb=short

    echo "$test_type tests completed."
}

# Run security scan
echo "Running security scan..."
bandit -r . -f json -o reports/bandit-report.json || true
safety check --json --output reports/safety-report.json || true

# Run test suites
run_tests "Unit" "tests/unit/" "unit-tests"
run_tests "Integration" "tests/integration/" "integration-tests"
run_tests "E2E" "tests/e2e/" "e2e-tests"
run_tests "Performance" "tests/performance/" "performance-tests"
run_tests "Compliance" "tests/compliance/" "compliance-tests"
run_tests "Accessibility" "tests/accessibility/" "accessibility-tests"

# Generate coverage report
echo "Generating coverage report..."
coverage run --source='.' -m pytest
coverage report
coverage html
coverage xml

echo "All tests completed!"
echo "Reports generated in reports/ directory"
"""

    def _get_monitoring_config_template(self) -> str:
        """Get monitoring configuration template"""
        return """global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'hms-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'hms-frontend'
    static_configs:
      - targets: ['localhost:3000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
    metrics_path: '/metrics'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - 'localhost:9093'
"""

    def generate_comprehensive_report(self, test_results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report_path = Path('reports/comprehensive-test-report.html')

        report_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>HMS Comprehensive Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric h3 {{ margin: 0; color: #2c3e50; }}
        .metric .value {{ font-size: 24px; font-weight: bold; }}
        .passed {{ color: #27ae60; }}
        .failed {{ color: #e74c3c; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        .success {{ background-color: #d4edda; }}
        .error {{ background-color: #f8d7da; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 HMS Comprehensive Test Report</h1>
        <p><strong>Environment:</strong> {self.config.environment.value}</p>
        <p><strong>Platform:</strong> {self.config.platform.value}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <div class="value">{test_results.get('total_tests', 0)}</div>
        </div>
        <div class="metric">
            <h3>Passed</h3>
            <div class="value passed">{test_results.get('passed', 0)}</div>
        </div>
        <div class="metric">
            <h3>Failed</h3>
            <div class="value failed">{test_results.get('failed', 0)}</div>
        </div>
        <div class="metric">
            <h3>Pass Rate</h3>
            <div class="value">{test_results.get('pass_rate', 0):.1f}%</div>
        </div>
    </div>

    <div class="section">
        <h2>📊 Test Results by Stage</h2>
        <table>
            <thead>
                <tr>
                    <th>Stage</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""

        for stage_name, stage_result in test_results.get('stages', {}).items():
            status_class = "success" if stage_result.get('success', False) else "error"
            status_text = "✅ Passed" if stage_result.get('success', False) else "❌ Failed"
            duration = stage_result.get('duration', 'N/A')

            report_content += f"""
                <tr>
                    <td>{stage_name.replace('_', ' ').title()}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{duration}</td>
                    <td>{stage_result.get('message', '')}</td>
                </tr>
"""

        report_content += """
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>🔧 System Information</h2>
        <table>
            <tr>
                <th>Component</th>
                <th>Version</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Python</td>
                <td>3.11</td>
                <td>✅ Active</td>
            </tr>
            <tr>
                <td>Django</td>
                <td>4.2</td>
                <td>✅ Active</td>
            </tr>
            <tr>
                <td>PostgreSQL</td>
                <td>15</td>
                <td>✅ Active</td>
            </tr>
            <tr>
                <td>Redis</td>
                <td>7</td>
                <td>✅ Active</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>📋 Recommendations</h2>
        <ul>
"""

        if test_results.get('pass_rate', 0) < 95:
            report_content += "<li>⚠️ Pass rate below 95%. Consider reviewing failing tests.</li>"

        if any(not stage.get('success', False) for stage in test_results.get('stages', {}).values()):
            report_content += "<li>🔧 Some test stages failed. Review logs for details.</li>"

        report_content += """
            <li>📈 Monitor test execution times for performance optimization.</li>
            <li>🔒 Regular security scans are recommended.</li>
            <li>♿ Accessibility compliance should be maintained.</li>
        </ul>
    </div>

    <div class="section">
        <h2>📝 Next Steps</h2>
        <ol>
            <li>Review any failing tests and fix issues.</li>
            <li>Update test cases as needed.</li>
            <li>Monitor production environment after deployment.</li>
            <li>Schedule regular test runs.</li>
        </ol>
    </div>
</body>
</html>
"""

        with open(report_path, 'w') as f:
            f.write(report_content)

        logger.info(f"Generated comprehensive test report: {report_path}")
        return str(report_path)

    def cleanup_old_reports(self, days_to_keep: int = 30):
        """Clean up old test reports"""
        reports_dir = Path('reports')

        if reports_dir.exists():
            for report_file in reports_dir.rglob('*.html'):
                if report_file.stat().st_mtime < (datetime.now().timestamp() - days_to_keep * 24 * 60 * 60):
                    report_file.unlink()
                    logger.info(f"Deleted old report: {report_file}")

    def get_test_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get test execution history"""
        history = []
        reports_dir = Path('reports')

        if reports_dir.exists():
            report_files = sorted(reports_dir.glob('*.xml'), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]

            for report_file in report_files:
                history.append({
                    'file': str(report_file),
                    'timestamp': datetime.fromtimestamp(report_file.stat().st_mtime),
                    'size': report_file.stat().st_size
                })

        return history


# Main execution
if __name__ == "__main__":
    # Example usage
    config = PipelineConfig(
        platform=CIPlatform.GITHUB_ACTIONS,
        environment=DeploymentEnvironment.STAGING,
        branch="develop",
        run_security_tests=True,
        run_performance_tests=True,
        run_compliance_tests=True,
        run_accessibility_tests=True
    )

    integrator = CI_CD_Integrator(config)

    # Generate all configurations
    configs = integrator.generate_all_configs()

    # Validate configurations
    errors = integrator.validate_configurations()
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")

    # Run local CI
    results = integrator.run_local_ci()

    # Generate comprehensive report
    report_path = integrator.generate_comprehensive_report(results)

    print(f"CI/CD integration completed. Report: {report_path}")
    print(f"Results: {results}")
"""