# Claude Code Tracer

> A development support tool that tracks and records Claude Code interactive sessions and stores them in Supabase

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

Claude Code Tracer is a system that automatically records and analyzes interactions with Claude Code (Anthropic's AI coding assistant). It supports developer productivity improvements, visualization of learning outcomes, and knowledge sharing within teams.

### Key Features

- 🔍 **Real-time Session Tracking**: Automatically records all Claude Code interactions
- 🛡️ **Privacy Protection**: Automatic detection and masking of sensitive information
- 📊 **Usage Pattern Analysis**: AI-driven analysis of development efficiency and insight generation
- 🔄 **GitHub Integration**: Automatic backup and history management
- 📈 **Dashboard**: Visual analysis results display via Web UI
- ⚡ **Real-time Sync**: Instant data updates via Supabase Realtime

## Quick Start

### Prerequisites

- Python 3.13 or higher
- Docker & Docker Compose
- Supabase account
- Claude Code CLI (installed)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/claude-code-tracer.git
cd claude-code-tracer

# Set up environment variables
cp .env.example .env
# Edit the .env file with your configuration

# Start development environment
make dev-setup
make dev-run
```

### Basic Usage

```bash
# Start Claude Code Tracer
python -m claude_code_tracer

# Start automatic tracking in background
claude-tracer start --daemon

# View session history
claude-tracer sessions list

# Show details of a specific session
claude-tracer sessions show <session-id>

# Launch Web dashboard
claude-tracer web
```

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Claude Code   │────│  Chat Logger    │────│    Supabase     │
│   (Terminal)    │    │     System      │    │   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                        │
                       ┌───────┴───────┐                │
                       │               │                │
                ┌─────────────┐ ┌─────────────┐         │
                │  Background │ │  Web UI     │         │
                │   Collector │ │ Dashboard   │         │
                └─────────────┘ └─────────────┘         │
                                       │                │
                               ┌───────┴────────────────┘
                               │
                        ┌─────────────┐
                        │   GitHub    │
                        │ Integration │
                        └─────────────┘
```

## Core Components

### 1. Session Monitor
Monitors Claude Code execution and collects session information in real-time

### 2. Privacy Guard
Automatically detects and masks sensitive information (API keys, passwords, personal information, etc.)

### 3. Analytics Engine
Analyzes usage patterns from collected data and generates development efficiency improvement suggestions

### 4. Supabase Integration
Provides real-time data synchronization and secure storage

## Configuration

### Environment Variables

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Claude Code Configuration
ANTHROPIC_API_KEY=your-api-key

# GitHub Integration (Optional)
GITHUB_TOKEN=your-personal-access-token
GITHUB_REPO=your-org/backup-repo

# Application Settings
LOG_LEVEL=INFO
PRIVACY_MODE=strict  # strict | moderate | minimal
AUTO_SYNC_INTERVAL=300  # in seconds
```

### Privacy Settings

You can define custom patterns in `config/privacy.yml`:

```yaml
custom_patterns:
  - pattern: 'COMPANY_SECRET_\w+'
    description: 'Company secret keys'
    replacement: '[COMPANY_SECRET]'
    level: MAXIMUM
```

## Development

### Project Structure

```
src/claude_code_tracer/
├── core/               # Core functionality
│   ├── monitor.py     # Session monitoring
│   ├── privacy.py     # Privacy protection
│   └── analyzer.py    # Data analysis
├── api/               # FastAPI endpoints
├── models/            # Data models
├── services/          # External service integrations
└── utils/            # Utilities
```

### Running Tests

```bash
# Unit tests
make test

# Integration tests
make test-integration

# Coverage report
make coverage
```

### Contributing

1. Fork and create a branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Create a Pull Request

## License

This project is published under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

- 📚 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-org/claude-code-tracer/issues)
- 💬 [Discussions](https://github.com/your-org/claude-code-tracer/discussions)

## Acknowledgments

- [Anthropic](https://anthropic.com) - Development of Claude Code
- [Supabase](https://supabase.com) - Real-time database infrastructure
- [vibe-logger](https://github.com/thierryvolpiatto/vibe-logger) - Inspiration for AI-native logging