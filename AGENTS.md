# HMS Enterprise-Grade System - Agent Guidelines

## Build/Lint/Test Commands
- **All tests**: `pytest`
- **Single test**: `pytest tests/unit/test_file.py::TestClass::test_method -v`
- **By marker**: `pytest -m "unit and not slow"` (markers: unit, integration, performance, security, slow, database, api)
- **Coverage**: `pytest --cov=. --cov-report=term-missing --cov-fail-under=95`
- **Frontend**: `npm test` (Jest + React Testing Library)
- **Quality analysis**: `make quality-analysis` or `python ultimate_code_quality_enforcer.py --target .`
- **Auto-fix**: `make auto-fix` (black + isort) or `pre-commit run --all-files`
- **Security scan**: `make security-scan` (bandit, safety, semgrep)
- **Pre-commit**: `pre-commit install && pre-commit run --all-files`

## Code Style Guidelines
- **Python**: Black (88 chars), isort (black profile), flake8, mypy (strict), bandit, pydocstyle (Google)
- **JavaScript/TypeScript**: ESLint (strict React/TS), Prettier (88 chars), TypeScript strict mode
- **Naming**: snake_case (Python), camelCase (JS/TS), PascalCase (classes/components)
- **Imports**: Grouped (FUTURE, STDLIB, THIRDPARTY, DJANGO, FIRSTPARTY, LOCALFOLDER) with blank lines
- **Types**: Strict typing required, TypeScript for frontend, mypy for Python, no Any types
- **Error handling**: Never expose sensitive data, use Django's exception handling, validate inputs
- **Security**: Django ORM only (no raw SQL), sanitize outputs, encrypt sensitive data, HIPAA compliance
- **Documentation**: Google-style docstrings (80% coverage), TypeScript JSDoc, interrogate checks
- **Quality gates**: 95% coverage, 0 critical issues, 85% test quality score, pre-commit passes