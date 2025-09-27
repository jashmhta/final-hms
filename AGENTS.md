# HMS Enterprise-Grade System - Agent Guidelines

## Build/Lint/Test Commands
- **All tests**: `pytest`
- **Single test**: `pytest tests/unit/test_models_comprehensive.py::TestClass::test_method -v`
- **Unit/Integration/Performance**: `pytest -m unit/integration/performance`
- **Coverage**: `pytest --cov=. --cov-report=term-missing --cov-fail-under=95`
- **Frontend tests**: `npm test` (if configured)
- **Quality analysis**: `make quality-analysis` or `python ultimate_code_quality_enforcer.py --target .`
- **Auto-fix**: `make auto-fix` (black + isort) or `pre-commit run --all-files`
- **Security scan**: `make security-scan` (bandit, safety, semgrep)
- **Pre-commit hooks**: `pre-commit install && pre-commit run --all-files`

## Code Style Guidelines
- **Python**: Black (88 chars), isort (black profile), flake8, mypy (strict), bandit
- **JavaScript/TypeScript**: ESLint (strict React/TS rules), Prettier (88 chars)
- **Naming**: snake_case (Python), camelCase (JS/TS), PascalCase (classes/components)
- **Imports**: Grouped (stdlib, third-party, local) with blank lines between groups
- **Types**: Strict typing required, use TypeScript for frontend, mypy for Python
- **Error handling**: Never expose sensitive data, use proper exceptions, validate inputs
- **Security**: Use Django ORM (no raw SQL), sanitize outputs, encrypt sensitive data
- **Documentation**: Google-style docstrings, 80% interrogate coverage, TypeScript JSDoc
- **Quality gates**: 95% coverage, 0 critical issues, 85% test quality score, HIPAA compliance