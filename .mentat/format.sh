#!/bin/bash
# Auto-format script run before commits

set -e

echo "Running auto-formatters..."

# Format Python code with black
if command -v black &> /dev/null; then
    echo "Running black..."
    black --line-length=88 backend/ || true
fi

# Sort Python imports with isort
if command -v isort &> /dev/null; then
    echo "Running isort..."
    isort --profile black backend/ || true
fi

# Format frontend code with prettier
if command -v npm &> /dev/null && [ -d "frontend" ]; then
    echo "Running prettier..."
    cd frontend && npm run format --if-present || true
    cd ..
fi

echo "Auto-formatting complete!"
