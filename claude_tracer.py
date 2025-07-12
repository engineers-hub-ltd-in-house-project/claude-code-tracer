#!/usr/bin/env python3
"""Claude Code Tracer - Monitor Claude Code sessions transparently."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_code_tracer.core.pty_monitor import PTYMonitor
from claude_code_tracer.utils.config import get_settings


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Claude Code Tracer - Transparently monitor and record Claude Code sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start monitoring Claude CLI
  python claude_tracer.py
  
  # Monitor with debug output
  python claude_tracer.py --debug
  
  # View recorded sessions
  python view_session.py --list
  python view_session.py <session-file>
        """
    )
    
    parser.add_argument("--command", type=str, default="claude", 
                       help="Command to monitor (default: claude)")
    parser.add_argument("--debug", action="store_true", 
                       help="Enable debug output to file")
    
    args = parser.parse_args()
    
    # Check configuration
    try:
        settings = get_settings()
        if settings.supabase_url == "https://demo-project.supabase.co":
            print("⚠️  Using local storage mode (no Supabase configured)")
            print("   Sessions will be saved to ./sessions/")
        else:
            print(f"✅ Supabase configured: {settings.supabase_url}")
    except Exception as e:
        print(f"⚠️  Configuration notice: {e}")
        print("   Sessions will be saved locally to ./sessions/")
    
    # Start PTY monitoring
    monitor = PTYMonitor(debug=args.debug)
    try:
        monitor.start_monitoring(args.command)
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()