# Claude Code Tracer - Makefile
# Development and deployment automation

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# === Environment Setup ===

.PHONY: install
install: ## Install dependencies using uv (recommended)
	uv pip install -e ".[dev]"

.PHONY: install-prod
install-prod: ## Install production dependencies only using uv
	uv pip install -e .

.PHONY: install-pip
install-pip: ## Install dependencies using pip
	pip install -r requirements-dev.txt

.PHONY: install-pip-prod
install-pip-prod: ## Install production dependencies only using pip
	pip install -r requirements.txt

.PHONY: poetry-install
poetry-install: ## Install dependencies using Poetry
	poetry install

.PHONY: uv-sync
uv-sync: ## Sync dependencies with requirements files using uv
	uv pip sync requirements-dev.txt

.PHONY: uv-compile
uv-compile: ## Compile requirements files from pyproject.toml using uv
	uv pip compile pyproject.toml -o requirements.txt
	uv pip compile pyproject.toml --extra dev -o requirements-dev.txt

.PHONY: setup
setup: install pre-commit-install ## Complete development environment setup
	cp -n .env.example .env || true
	@echo "Setup complete! Edit .env file with your configuration."

# === Development ===

.PHONY: dev
dev: ## Run development server
	uv run python -m claude_code_tracer --debug

.PHONY: dev-api
dev-api: ## Run FastAPI development server with auto-reload
	uv run uvicorn claude_code_tracer.api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: dev-monitor
dev-monitor: ## Run Claude Code monitor in development mode
	uv run python -m claude_code_tracer.core.monitor --debug

# === Docker ===

.PHONY: docker-build
docker-build: ## Build Docker images
	docker-compose build

.PHONY: docker-up
docker-up: ## Start all services with Docker Compose
	docker-compose up -d

.PHONY: docker-down
docker-down: ## Stop all Docker services
	docker-compose down

.PHONY: docker-logs
docker-logs: ## View Docker logs
	docker-compose logs -f

.PHONY: docker-clean
docker-clean: ## Clean Docker resources
	docker-compose down -v
	docker system prune -f

# === Database ===

.PHONY: db-setup
db-setup: ## Initialize database schema
	uv run python scripts/setup_db.py

.PHONY: db-migrate
db-migrate: ## Run database migrations
	uv run python scripts/migrate.py

.PHONY: db-seed
db-seed: ## Seed database with sample data
	uv run python scripts/seed_db.py

.PHONY: db-reset
db-reset: ## Reset database (WARNING: destroys all data)
	@echo "WARNING: This will destroy all data. Press Ctrl+C to cancel, or Enter to continue."
	@read confirm
	uv run python scripts/reset_db.py

# === Testing ===

.PHONY: test
test: ## Run unit tests
	uv run pytest tests/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests
	uv run pytest tests/integration -v

.PHONY: test-all
test-all: ## Run all tests with coverage
	uv run pytest -v --cov=claude_code_tracer --cov-report=html --cov-report=term

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	uv run ptw -- -v

.PHONY: coverage
coverage: test-all ## Generate coverage report
	@echo "Coverage report generated in htmlcov/index.html"
	@python -m webbrowser htmlcov/index.html

# === Code Quality ===

.PHONY: format
format: ## Format code with black and isort
	uv run black src tests scripts
	uv run isort src tests scripts

.PHONY: lint
lint: ## Run linters (ruff)
	uv run ruff check src tests scripts

.PHONY: lint-fix
lint-fix: ## Fix linting issues automatically
	uv run ruff check --fix src tests scripts

.PHONY: type-check
type-check: ## Run type checking with mypy
	uv run mypy src

.PHONY: quality
quality: format lint type-check ## Run all code quality checks

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

.PHONY: pre-commit-install
pre-commit-install: ## Install pre-commit hooks
	pre-commit install

# === Documentation ===

.PHONY: docs
docs: ## Build documentation
	cd docs && mkdocs build

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	cd docs && mkdocs serve

# === Build & Release ===

.PHONY: build
build: clean ## Build distribution packages
	python -m build

.PHONY: publish-test
publish-test: build ## Publish to TestPyPI
	python -m twine upload --repository testpypi dist/*

.PHONY: publish
publish: build ## Publish to PyPI (requires authentication)
	python -m twine upload dist/*

# === Monitoring ===

.PHONY: metrics
metrics: ## Start Prometheus metrics server
	uv run python -m claude_code_tracer.monitoring.metrics

.PHONY: monitor-start
monitor-start: ## Start background monitoring daemon
	uv run claude-tracer start --daemon

.PHONY: monitor-stop
monitor-stop: ## Stop background monitoring daemon
	uv run claude-tracer stop

.PHONY: monitor-status
monitor-status: ## Check monitoring daemon status
	uv run claude-tracer status

# === Utilities ===

.PHONY: clean
clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

.PHONY: secrets-check
secrets-check: ## Check for exposed secrets
	@echo "Checking for exposed secrets..."
	@grep -r "SUPABASE_SERVICE_ROLE_KEY\|ANTHROPIC_API_KEY\|GITHUB_TOKEN\|SECRET_KEY" src tests scripts || echo "No secrets found in code."

.PHONY: update-deps
update-deps: ## Update dependencies to latest versions
	uv pip compile pyproject.toml --upgrade -o requirements.txt
	uv pip compile pyproject.toml --extra dev --upgrade -o requirements-dev.txt

.PHONY: shell
shell: ## Start Python shell with project context
	uv run python -m IPython

.PHONY: logs
logs: ## Tail application logs
	tail -f logs/claude-tracer.log

.PHONY: backup
backup: ## Create backup of local data
	uv run python scripts/backup.py

# === CI/CD ===

.PHONY: ci
ci: quality test-all ## Run all CI checks

.PHONY: release
release: ## Create a new release (requires version bump)
	@echo "Current version: $$(poetry version -s)"
	@echo "Enter new version: "
	@read VERSION && poetry version $$VERSION
	git add pyproject.toml
	git commit -m "Bump version to $$(poetry version -s)"
	git tag -a "v$$(poetry version -s)" -m "Release version $$(poetry version -s)"
	@echo "Version bumped. Run 'git push && git push --tags' to push changes."