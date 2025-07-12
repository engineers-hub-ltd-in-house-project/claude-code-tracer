"""
Claude Code Tracer - Main entry point
"""

import asyncio
import logging
import sys
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from .cli import cli
from .utils.config import get_settings
from .utils.logging import setup_logging

console = Console()


def setup_environment():
    """Initialize environment and logging"""
    settings = get_settings()
    setup_logging(settings.log_level)
    
    # Configure rich logging
    logging.basicConfig(
        level=settings.log_level,
        format="%(message)s",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                tracebacks_show_locals=settings.debug
            )
        ]
    )


@click.group()
@click.version_option(version="0.1.0", prog_name="claude-code-tracer")
@click.pass_context
def main(ctx):
    """Claude Code Tracer - Track and analyze Claude Code interactions"""
    setup_environment()
    ctx.ensure_object(dict)


@main.command()
@click.option("--daemon", is_flag=True, help="Run in daemon mode")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def start(daemon: bool, debug: bool):
    """Start the Claude Code monitoring service"""
    from .core.monitor import start_monitoring
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if daemon:
            console.print("[green]Starting Claude Code Tracer in daemon mode...[/green]")
            # TODO: Implement proper daemon mode
            asyncio.run(start_monitoring())
        else:
            console.print("[green]Starting Claude Code Tracer...[/green]")
            asyncio.run(start_monitoring())
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
def stop():
    """Stop the Claude Code monitoring service"""
    # TODO: Implement stop functionality
    console.print("[yellow]Stop command not yet implemented[/yellow]")


@main.command()
def status():
    """Check the status of the monitoring service"""
    # TODO: Implement status check
    console.print("[yellow]Status command not yet implemented[/yellow]")


@main.group()
def sessions():
    """Manage Claude Code sessions"""
    pass


@sessions.command("list")
@click.option("--limit", default=10, help="Number of sessions to display")
@click.option("--status", help="Filter by status (active, completed, error)")
def list_sessions(limit: int, status: Optional[str]):
    """List recent Claude Code sessions"""
    from .cli.sessions import list_sessions as _list_sessions
    
    asyncio.run(_list_sessions(limit, status))


@sessions.command("show")
@click.argument("session_id")
def show_session(session_id: str):
    """Show details of a specific session"""
    from .cli.sessions import show_session as _show_session
    
    asyncio.run(_show_session(session_id))


@main.command()
@click.option("--host", default="0.0.0.0", help="Web server host")
@click.option("--port", default=8000, help="Web server port")
def web(host: str, port: int):
    """Start the web dashboard"""
    import uvicorn
    
    console.print(f"[green]Starting web dashboard at http://{host}:{port}[/green]")
    uvicorn.run(
        "claude_code_tracer.api.main:app",
        host=host,
        port=port,
        reload=True
    )


if __name__ == "__main__":
    main()