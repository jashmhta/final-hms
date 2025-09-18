SHELL := /bin/bash

.PHONY: help generate-keys up down logs bootstrap seed quality-analysis install-tools run-analysis quality-gates continuous-analysis generate-reports cleanup setup-all setup-dev setup-prod security-scan complexity-analysis coverage-analysis performance-analysis documentation-analysis duplication-analysis static-analysis auto-fix technical-debt-report compliance-check healthcare-compliance security-compliance performance-compliance deployment-compliance monitoring-dashboard

help:
	@echo "HMS Enterprise-Grade System - Quality Management Makefile"
	@echo "=========================================================="
	@echo ""
	@echo "Docker Operations:"
	@echo "  generate-keys    Generate RSA keypair in ./keys for audit encryption"
	@echo "  up               Start docker-compose stack"
	@echo "  down             Stop docker-compose stack"
	@echo "  logs             Tail logs"
	@echo "  seed             Seed demo data (run after up)"
	@echo "  bootstrap        Generate keys and start services"
	@echo ""
	@echo "Quality Analysis:"
	@echo "  quality-analysis  Run comprehensive quality analysis"
	@echo "  install-tools     Install all quality analysis tools"
	@echo "  run-analysis      Run comprehensive analysis"
	@echo "  quality-gates     Check quality gates"
	@echo "  static-analysis   Run static code analysis"
	@echo "  security-scan     Run security scanning"
	@echo "  complexity-analysis Run complexity analysis"
	@echo "  coverage-analysis Run coverage analysis"
	@echo ""
	@echo "Healthcare Compliance:"
	@echo "  healthcare-compliance Check healthcare compliance"
	@echo "  security-compliance  Check security compliance"
	@echo ""
	@echo "Automation:"
	@echo "  auto-fix           Apply automatic fixes"
	@echo "  continuous-analysis Run continuous analysis"
	@echo "  generate-reports   Generate quality reports"
	@echo ""
	@echo "Setup & Cleanup:"
	@echo "  setup-all          Setup complete environment"
	@echo "  cleanup            Clean up temporary files"

KEY_DIR := keys
PUB := $(KEY_DIR)/audit_public.pem
PRIV := $(KEY_DIR)/audit_private.pem

# Quality Analysis Targets
quality-analysis:
	@echo "Running comprehensive quality analysis..."
	python ultimate_code_quality_enforcer.py --target .

install-tools:
	@echo "Installing code quality tools..."
	pip install -r requirements_code_quality.txt
	npm install -g eslint prettier typescript @typescript-eslint/parser @typescript-eslint/eslint-plugin
	@echo "Quality tools installed successfully!"

run-analysis:
	@echo "Running comprehensive analysis..."
	python ultimate_code_quality_enforcer.py --target .

quality-gates:
	@echo "Checking quality gates..."
	python ultimate_code_quality_enforcer.py --target . --report-only

continuous-analysis:
	@echo "Starting continuous quality analysis..."
	python ultimate_code_quality_enforcer.py --target . --continuous --interval 3600

generate-reports:
	@echo "Generating quality reports..."
	python ultimate_code_quality_enforcer.py --target . --report-only

static-analysis:
	@echo "Running static code analysis..."
	sonar-scanner -Dsonar.login=${SONAR_TOKEN} || echo "SonarQube requires authentication"
	semgrep --config=.semgrep.yml --json --output=semgrep-results.json .
	bandit -r . -f json -o bandit-results.json || true
	@echo "Static analysis complete!"

security-scan:
	@echo "Running security scanning..."
	snyk test --json > snyk-results.json || true
	safety check --json --output safety-results.json || true
	bandit -r . -f json -o bandit-security-results.json || true
	@echo "Security scanning complete!"

complexity-analysis:
	@echo "Running complexity analysis..."
	python complexity_analysis.py
	@echo "Complexity analysis complete!"

coverage-analysis:
	@echo "Running coverage analysis..."
	python coverage_config.py
	@echo "Coverage analysis complete!"

performance-analysis:
	@echo "Running performance analysis..."
	python -m cProfile -o performance_profile.prof ultimate_code_quality_enforcer.py
	@echo "Performance analysis complete!"

documentation-analysis:
	@echo "Running documentation analysis..."
	interrogate --verbose --ignore-init-module --ignore-module --ignore-private . || true
	@echo "Documentation analysis complete!"

duplication-analysis:
	@echo "Running duplication analysis..."
	jscpd --format python --max-duplicates 5 --output json --output-file jscpd-results.json . || true
	@echo "Duplication analysis complete!"

auto-fix:
	@echo "Applying automatic fixes..."
	black .
	isort .
	@echo "Auto-fix complete!"

technical-debt-report:
	@echo "Generating technical debt report..."
	python ultimate_code_quality_enforcer.py --target . --config .quality_config.json
	@echo "Technical debt report generated!"

compliance-check:
	@echo "Running compliance check..."
	python ultimate_code_quality_enforcer.py --target . --config .quality_config.json
	@echo "Compliance check complete!"

healthcare-compliance:
	@echo "Checking healthcare compliance..."
	python ultimate_code_quality_enforcer.py --target . --config .quality_config.json
	@echo "Healthcare compliance check complete!"

security-compliance:
	@echo "Checking security compliance..."
	python ultimate_code_quality_enforcer.py --target . --config .quality_config.json
	@echo "Security compliance check complete!"

performance-compliance:
	@echo "Checking performance compliance..."
	python ultimate_code_quality_enforcer.py --target . --config .quality_config.json
	@echo "Performance compliance check complete!"

deployment-compliance:
	@echo "Checking deployment compliance..."
	python ultimate_code_quality_enforcer.py --target . --config .quality_config.json
	@echo "Deployment compliance check complete!"

monitoring-dashboard:
	@echo "Generating monitoring dashboard..."
	python ultimate_code_quality_enforcer.py --target . --config .quality_config.json
	@echo "Monitoring dashboard generated!"

setup-all:
	@echo "Setting up complete HMS Enterprise-Grade environment..."
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements_code_quality.txt
	npm install
	pre-commit install
	@echo "Environment setup complete!"

setup-dev: setup-all
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "Development environment setup complete!"

setup-prod: setup-all
	@echo "Setting up production environment..."
	cp .env.production .env
	@echo "Production environment setup complete!"

cleanup:
	@echo "Cleaning up temporary files..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.egg-info" -type d -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete
	find . -name "htmlcov" -type d -exec rm -rf {} +
	find . -name ".pytest_cache" -type d -exec rm -rf {} +
	find . -name "*.prof" -delete
	find . -name "*.sarif" -delete
	rm -rf build/ dist/ *.egg-info/
	rm -f .coverage coverage.xml coverage.json
	rm -rf htmlcov/
	rm -rf reports/
	rm -rf audits/
	rm -rf .pytest_cache/
	rm -f *.prof
	rm -f memory_profile.txt
	@echo "Cleanup complete!"

# Docker Operations (Original targets)
$(KEY_DIR):
	mkdir -p $(KEY_DIR)

$(PRIV): | $(KEY_DIR)
	openssl genrsa -out $(PRIV) 2048

$(PUB): $(PRIV)
	openssl rsa -in $(PRIV) -pubout -out $(PUB)

generate-keys: $(PUB)
	@echo "Keys generated at $(KEY_DIR)"

up:
	docker compose up -d

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

seed:
	docker compose exec backend python manage.py migrate --noinput || true
	docker compose exec backend python manage.py seed_demo

bootstrap: generate-keys up
	@echo "Stack started. Grafana at http://localhost:3001, Prometheus at http://localhost:9090"
