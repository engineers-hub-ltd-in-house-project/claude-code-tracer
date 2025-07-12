"""Main entry point for Claude Code Tracer package."""

import sys
import asyncio
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_code_tracer.api.main import app
from claude_code_tracer.utils.config import get_settings


def main():
    """Main CLI entry point."""
    import uvicorn
    import click
    
    @click.group()
    def cli():
        """Claude Code Tracer - Monitor and analyze your Claude Code sessions."""
        pass
    
    @cli.command()
    @click.option('--host', default='0.0.0.0', help='Host to bind to')
    @click.option('--port', default=8000, help='Port to bind to')
    @click.option('--reload', is_flag=True, help='Enable auto-reload')
    def api(host, port, reload):
        """Start the FastAPI server."""
        settings = get_settings()
        
        print(f"🚀 Starting Claude Code Tracer API on {host}:{port}")
        print(f"📝 Docs available at: http://{host}:{port}/docs")
        
        uvicorn.run(
            "claude_code_tracer.api.main:app",
            host=host,
            port=port,
            reload=reload or settings.api_reload,
            log_level=settings.log_level.lower(),
        )
    
    @cli.command()
    def monitor():
        """Start the Claude Code monitor (mock mode for now)."""
        print("⚠️  Note: claude-code-sdk is not a real package.")
        print("🔧 Running in mock mode for demonstration...")
        
        # For now, just show what would happen
        print("\n📝 Monitor would:")
        print("  - Watch for Claude Code sessions")
        print("  - Apply privacy protection")
        print("  - Save to Supabase")
        print("\n💡 To test the API instead, run: python -m claude_code_tracer api")
    
    @cli.command()
    def setup_db():
        """Set up the database schema."""
        import subprocess
        
        print("🗄️  Setting up database schema...")
        try:
            subprocess.run([sys.executable, "scripts/setup_db.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Database setup failed: {e}")
            sys.exit(1)
    
    @cli.command()
    def check():
        """Check configuration and dependencies."""
        print("🔍 Checking Claude Code Tracer configuration...")
        
        try:
            settings = get_settings()
            print("✅ Configuration loaded successfully")
            print(f"   - Privacy mode: {settings.privacy_mode}")
            print(f"   - Log level: {settings.log_level}")
            print(f"   - Supabase URL: {settings.supabase_url}")
            
            # Check if .env exists
            if not Path(".env").exists():
                print("\n⚠️  Warning: .env file not found")
                print("   Run: cp .env.example .env")
                print("   Then edit .env with your credentials")
            
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            print("\n💡 Make sure to:")
            print("   1. Copy .env.example to .env")
            print("   2. Fill in your Supabase and API credentials")
            sys.exit(1)
    
    # Run the CLI
    cli()


if __name__ == "__main__":
    main()