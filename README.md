# Claude Code Tracer 🔍 [ARCHIVED]

> **⚠️ This project is archived as of 2025-07-13**
> 
> **Status**: Development suspended due to technical limitations with Claude CLI's complex UI rendering.
> 
> **Issue**: Claude CLI uses a rich, animated terminal UI that makes clean text extraction extremely difficult through PTY monitoring. The constant screen updates, animations (Honking, Processing, Wrangling), and complex ANSI escape sequences prevent reliable capture of conversation content.
> 
> **Future**: Waiting for official logging/monitoring features from Anthropic Claude CLI team.

<pre>
╭─────────────────────────────────────────────────────────────────────╮
│                                                                     │
│   ┌─────────────┐      ┌──────────────────┐      ┌──────────────┐ │
│   │ Claude CLI  │ ───▶ │ Claude Code      │ ───▶ │   Session    │ │
│   │   (claude)  │      │     Tracer       │      │   Storage    │ │
│   └─────────────┘      └──────────────────┘      └──────────────┘ │
│         │                       │                         │         │
│         │                       │                         │         │
│         ▼                       ▼                         ▼         │
│   ╔═══════════╗          ╔═══════════╗            ╔═══════════╗   │
│   ║   User    ║          ║ PTY Magic ║            ║   Local/  ║   │
│   ║ Terminal  ║          ║ Monitors  ║            ║ Supabase  ║   │
│   ╚═══════════╝          ╚═══════════╝            ╚═══════════╝   │
│                                                                     │
╰─────────────────────────────────────────────────────────────────────╯
</pre>

**Transparently monitor and record Claude CLI sessions** 🎯

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## ✨ Features

- 🔒 **Completely transparent** - Claude CLI usage remains exactly the same
- 📝 **Automatic recording** - Captures all conversations automatically
- 🛡️ **Privacy protection** - Auto-masks API keys and personal information
- 💾 **Flexible storage** - Local or Supabase storage options
- 🎨 **Clean display** - Removes UI decorations for essential content only

## 🚀 Quick Start

### 1. Start monitoring Claude CLI

```bash
# Run in terminal
$ python claude_tracer.py

⚠️  Using local storage mode (no Supabase configured)
   Sessions will be saved to ./sessions/
🚀 Claude Code Tracer - PTY Monitor
==================================================
📝 Session ID: pty-20250712-223357
📁 Logs saved to: sessions/pty-20250712-223357.json
==================================================
Starting claude...

╭────────────────────────────────────────────────────────────────────────────╮
│ ✻ Welcome to Claude Code!                                                  │
│                                                                            │
│   /help for help, /status for your current setup                           │
│                                                                            │
│   cwd: /home/user/project                                                  │
╰────────────────────────────────────────────────────────────────────────────╯

> [Use Claude normally as usual!]
```

### 2. View sessions

```bash
# List all sessions
$ python view_session.py --list

📂 Available Sessions:
----------------------------------------------------------------------
1. pty-20250712-223357.json
   Time: 2025-07-12 22:33:57 | Interactions: 2 | Status: completed
2. pty-20250712-221234.json
   Time: 2025-07-12 22:12:34 | Interactions: 5 | Status: completed

# View specific session
$ python view_session.py pty-20250712-223357.json

🔍 Claude Code Tracer Session Viewer
======================================================================
📋 Session ID: pty-20250712-223357
📁 Project: /home/user/project
🕐 Start: 2025-07-12 22:33:57
🕑 End: 2025-07-12 22:34:33
📊 Total interactions: 2
🔧 Monitor type: pty
======================================================================

### Interaction 1 [2025-07-12 22:34:08]
----------------------------------------------------------------------
👤 USER:
   Write a Python function to generate Fibonacci sequence

🤖 CLAUDE:
   Here are several ways to implement a Fibonacci sequence generator:

   def fibonacci_iterative(n):
       """Generate Fibonacci sequence up to n terms using iteration"""
       if n <= 0:
           return []
       elif n == 1:
           return [0]
       
       fib = [0, 1]
       for i in range(2, n):
           fib.append(fib[i-1] + fib[i-2])
       return fib[:n]
----------------------------------------------------------------------
```

## 📦 Installation

### Prerequisites

- Python 3.13+
- Claude CLI (`claude` command) installed and working

### Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/claude-code-tracer.git
cd claude-code-tracer

# 2. Install dependencies (choose one)

# Using pip
pip install -r requirements.txt

# Using uv (recommended)
uv pip install -e .

# Using poetry
poetry install

# 3. Environment setup (optional, for Supabase)
cp .env.example .env
# Edit .env to configure Supabase credentials
```

## 🔧 Configuration

### Local Storage Mode (Default)

No configuration needed! Sessions are automatically saved to `./sessions/` directory.

### Supabase Mode

To use Supabase, configure `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Privacy Settings (optional)
PRIVACY_MODE=strict  # strict, moderate, minimal
```

## 🛡️ Privacy Protection

The following information is automatically masked:

- API keys (OpenAI, Anthropic, GitHub, etc.)
- Database connection strings
- Email addresses
- Phone numbers
- Credit card numbers
- IP addresses
- Passwords

Custom patterns can be configured in `config/privacy.yml`:

```yaml
custom_patterns:
  - name: "Company API Key"
    pattern: 'INTERNAL_API_[A-Z0-9]+'
    replacement: "[INTERNAL_API]"
    level: HIGH
```

## 🏗️ Architecture

```
claude-code-tracer/
├── claude_tracer.py      # Main entry point
├── view_session.py       # Session viewer
├── src/
│   └── claude_code_tracer/
│       ├── core/
│       │   ├── pty_monitor.py    # PTY-based monitoring
│       │   └── privacy.py        # Privacy protection
│       ├── models/               # Data models
│       ├── services/             # Supabase integration
│       └── utils/                # Utilities
├── sessions/             # Local session storage
├── config/
│   └── privacy.yml       # Privacy pattern configuration
└── docs/                 # Documentation
```

## 💡 Usage Examples

### Basic Usage

```bash
# Monitor Claude CLI
python claude_tracer.py

# Run with debug output (for troubleshooting)
python claude_tracer.py --debug

# Monitor different command
python claude_tracer.py --command "python"
```

### Session Management

```bash
# List recent sessions
python view_session.py --list

# View specific session
python view_session.py sessions/pty-20250712-223357.json

# Export sessions (planned feature)
python export_sessions.py --format markdown
```

## 📊 Session Data Format

Sessions are stored in the following JSON format:

```json
{
  "id": "pty-20250712-223357",
  "session_id": "pty-20250712-223357",
  "project_path": "/home/user/project",
  "start_time": "2025-07-12T13:33:57.558350",
  "end_time": "2025-07-12T13:34:33.201156",
  "status": "completed",
  "total_interactions": 2,
  "interactions": [
    {
      "id": "int-0",
      "sequence_number": 0,
      "timestamp": "2025-07-12T13:34:08.637982",
      "user_prompt": "Write a Python function...",
      "claude_response": "Here are several ways to...",
      "message_type": "interaction"
    }
  ],
  "metadata": {
    "monitor_type": "pty",
    "command": "claude"
  }
}
```

## 🔍 Troubleshooting

### Claude CLI not found

```bash
# Check claude command path
which claude

# Use specific path
python claude_tracer.py --command /path/to/claude
```

### Sessions not being recorded

```bash
# Run with debug mode
python claude_tracer.py --debug

# Check debug logs
cat sessions/debug-*.log
```

### Privacy settings verification

```bash
# Check current configuration
cat config/privacy.yml

# Test privacy patterns
python -m claude_code_tracer.core.privacy --test
```

## 📚 Documentation

- [Architecture Design](docs/architecture.md) - System design details
- [Setup Guide](docs/setup.md) - Detailed installation instructions
- [Usage Guide](docs/usage.md) - Advanced usage methods
- [API Reference](docs/api.md) - Programmatic usage
- [Development Guide](docs/development.md) - Contributor guide

## 🤝 Contributing

Pull requests are welcome!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) - For developing Claude CLI
- [Supabase](https://supabase.com) - Real-time database infrastructure
- Various open source projects for PTY implementation inspiration

---

<div align="center">
Made with ❤️ for the Claude Code community
</div>