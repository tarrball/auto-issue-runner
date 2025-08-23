# Auto Issue Runner - Development Commands

.PHONY: install format lint typecheck test clean run help

help: ## Show this help message
	@echo "Auto Issue Runner - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install package and dev dependencies
	pip install -e .[dev]

format: ## Format code with black
	black .

lint: ## Lint code with ruff
	ruff check . --fix

typecheck: ## Type check with mypy
	mypy .

test: ## Run tests with pytest
	pytest

check: format lint typecheck test ## Run all checks (format, lint, typecheck, test)

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the application
	python -m auto_issue_runner.main

dev-setup: ## Setup development environment
	python -m venv venv
	@echo "Activate with: source venv/bin/activate"
	@echo "Then run: make install"