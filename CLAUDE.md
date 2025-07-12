# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Unit tests
make test

# Integration tests  
make test-integration

# All tests with coverage
make test-all

# Watch mode for tests
make test-watch
```

### Code Quality
```bash
# Format code with black and isort
make format

# Run linters (ruff)
make lint

# Fix linting issues automatically
make lint-fix

# Type checking with mypy
make type-check

# Run all quality checks
make quality
```

### Running the Application
```bash
# Development mode
make dev

# FastAPI server with auto-reload
make dev-api

# Claude Code monitor
make dev-monitor

# Background monitoring daemon
make monitor-start
make monitor-stop
make monitor-status
```

### Docker Operations
```bash
# Build and run with Docker
make docker-build
make docker-up
make docker-down
make docker-logs
```

### Database Operations
```bash
# Initialize database
make db-setup

# Run migrations
make db-migrate

# Seed sample data
make db-seed

# Reset database (WARNING: destroys data)
make db-reset
```

## Architecture Overview

This project is a monitoring and analytics system for Claude Code interactions, built with:

- **Core Monitor**: Uses `claude-code-sdk` to track Claude Code sessions in real-time
- **Privacy Guard**: Automatically detects and masks sensitive information (API keys, passwords, PII)
- **Supabase Integration**: Real-time data persistence and synchronization
- **FastAPI Backend**: RESTful API for data access and analytics
- **Analytics Engine**: Generates insights from collected session data

### Key Components

1. **Session Monitoring** (`src/claude_code_tracer/core/monitor.py`)
   - Tracks Claude Code sessions using the SDK
   - Captures user prompts and Claude responses
   - Records tool usage and performance metrics

2. **Privacy Protection** (`src/claude_code_tracer/core/privacy.py`)
   - Pattern-based sensitive data detection
   - Configurable security levels (strict/moderate/minimal)
   - Custom pattern support via `config/privacy.yml`

3. **Data Flow**
   - Claude Code SDK → Monitor → Privacy Guard → Supabase
   - Real-time updates via Supabase Realtime subscriptions
   - Optional GitHub backup for session history

## Dependency Management

This project supports uv (recommended), Poetry, and pip:

### uv (Recommended)
```bash
uv pip install -e .              # Install project in editable mode
uv pip install -e ".[dev]"       # Install with dev dependencies
uv pip sync requirements.txt     # Install from requirements file
uv pip compile pyproject.toml -o requirements.txt  # Generate requirements.txt
uv run python -m claude_code_tracer  # Run commands in uv environment
```

### Poetry
```bash
poetry install          # Install all dependencies
poetry add <package>    # Add new dependency
poetry update          # Update dependencies
```

### Pip
```bash
pip install -r requirements-dev.txt  # Development
pip install -r requirements.txt      # Production only
```

## Environment Setup

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```

2. Configure required variables:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Supabase anon key
   - `SUPABASE_SERVICE_ROLE_KEY`: Service role key
   - `ANTHROPIC_API_KEY`: For Claude Code SDK
   - `PRIVACY_MODE`: strict/moderate/minimal
   - `GITHUB_TOKEN`: Optional, for backup integration

3. Initialize development environment:
   ```bash
   make setup
   ```

## Python Version

This project requires Python 3.13+ and uses modern Python features including:
- Type hints with full mypy strict mode
- Async/await for concurrent operations
- Pydantic v2 for data validation
- Modern tooling (black, ruff, poetry)