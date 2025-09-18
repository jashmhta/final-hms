import js from '@eslint/js';
import typescript from '@typescript-eslint/eslint-plugin';
import typescriptParser from '@typescript-eslint/parser';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import jsxAccessibility from 'eslint-plugin-jsx-a11y';
import importPlugin from 'eslint-plugin-import';
import promise from 'eslint-plugin-promise';
import security from 'eslint-plugin-security';
import sonarjs from 'eslint-plugin-sonarjs';
import unicorn from 'eslint-plugin-unicorn';
import preferArrow from 'eslint-plugin-prefer-arrow';
import noSecrets from 'eslint-plugin-no-secrets';
export default [
  js.configs.recommended,
  {
    files: ['***.ts', '***.test.{js,jsx,ts,tsx}'],
    languageOptions: {
      globals: {
        describe: 'readonly',
        it: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        jest: 'readonly',
        beforeAll: 'readonly',
        afterAll: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
      },
    },
    rules: {
      'sonarjs/no-duplicate-string': 'off',
      'max-lines-per-function': 'off',
      'max-lines': 'off',
    },
  },
  {
    files: ['***.config.ts'],
    rules: {
      'import/no-extraneous-dependencies': 'off',
      'no-console': 'off',
    },
  },
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'build/**',
      'coverage/**',
      '.git/**',
      '*.min.js',
      'vendor/**',
      'public/**',
      'out/**',
      '.next/**',
      '.nuxt/**',
      '.vscode/**',
      '.idea/**',
      '*.log',
      '*.tmp',
      '*.temp',
      'Dockerfile*',
      'docker-compose*',
      '*.yml',
      '*.yaml',
      'k8s/**',
      'helm/**',
      'docs/**',
      'README.md',
      'CHANGELOG.md',
      'LICENSE',
      'NOTICE',
      'package-lock.json',
      'yarn.lock',
      'pnpm-lock.yaml',
      'requirements*.txt',
      'Pipfile*',
      'poetry.lock',
      'pyproject.toml',
      'venv/**',
      'env/**',
      '.env*',
      '*.pyc',
      '__pycache__/**',
      '.pytest_cache/**',
      '.mypy_cache/**',
      '.coverage',
      'coverage.xml',
      'htmlcov/**',
      '.tox/**',
      '.pytest_cache/**',
      '.mypy_cache/**',
      '.coverage',
      'coverage.xml',
      'htmlcov/**',
      '.tox/**',
    ],
  },
];