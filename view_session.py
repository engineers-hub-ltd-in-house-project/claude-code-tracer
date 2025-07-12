#!/usr/bin/env python3
"""View Claude Code Tracer sessions in a readable format."""

import json
import sys
from pathlib import Path
from datetime import datetime
import argparse


def format_timestamp(iso_timestamp):
    """Format ISO timestamp to readable format."""
    dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def view_session(session_file):
    """Display session in readable format."""
    with open(session_file, 'r') as f:
        session = json.load(f)
    
    print(f"🔍 Claude Code Tracer Session Viewer")
    print("=" * 70)
    print(f"📋 Session ID: {session['session_id']}")
    print(f"📁 Project: {session['project_path']}")
    print(f"🕐 Start: {format_timestamp(session['start_time'])}")
    if 'end_time' in session:
        print(f"🕑 End: {format_timestamp(session['end_time'])}")
    print(f"📊 Total interactions: {session.get('total_interactions', len(session['interactions']))}")
    print(f"🔧 Monitor type: {session['metadata'].get('monitor_type', 'unknown')}")
    print("=" * 70)
    
    # Display interactions
    for i, interaction in enumerate(session['interactions']):
        print(f"\n### Interaction {i + 1} [{format_timestamp(interaction['timestamp'])}]")
        print("-" * 70)
        
        # User prompt
        print(f"👤 USER:")
        print(f"   {interaction['user_prompt']}")
        print()
        
        # Claude response
        if interaction.get('claude_response'):
            print(f"🤖 CLAUDE:")
            # Split response into lines for better formatting
            response_lines = interaction['claude_response'].split('\n')
            for line in response_lines:
                if line.strip():
                    print(f"   {line}")
        
        print("-" * 70)
    
    print(f"\n✅ Session viewer completed")


def list_sessions(sessions_dir):
    """List all available sessions."""
    sessions_dir = Path(sessions_dir)
    session_files = sorted(sessions_dir.glob("pty-*.json"), reverse=True)
    
    if not session_files:
        print("No sessions found.")
        return
    
    print("📂 Available Sessions:")
    print("-" * 70)
    
    for i, session_file in enumerate(session_files[:10]):  # Show last 10
        try:
            with open(session_file, 'r') as f:
                session = json.load(f)
            
            timestamp = format_timestamp(session['start_time'])
            interactions = len(session['interactions'])
            status = session.get('status', 'unknown')
            
            print(f"{i+1}. {session_file.name}")
            print(f"   Time: {timestamp} | Interactions: {interactions} | Status: {status}")
        except Exception as e:
            print(f"{i+1}. {session_file.name} (Error reading: {e})")
    
    if len(session_files) > 10:
        print(f"\n... and {len(session_files) - 10} more sessions")


def main():
    parser = argparse.ArgumentParser(description="View Claude Code Tracer sessions")
    parser.add_argument("session", nargs="?", help="Session file to view")
    parser.add_argument("--list", "-l", action="store_true", help="List available sessions")
    parser.add_argument("--dir", default="./sessions", help="Sessions directory")
    parser.add_argument("--raw", action="store_true", help="Show raw output (with UI elements)")
    
    args = parser.parse_args()
    
    if args.list or not args.session:
        list_sessions(args.dir)
        if not args.session:
            print("\nUsage: python view_session.py <session-file>")
            print("   or: python view_session.py --list")
    else:
        session_path = Path(args.session)
        if not session_path.exists():
            # Try in sessions directory
            session_path = Path(args.dir) / args.session
        
        if session_path.exists():
            view_session(session_path)
        else:
            print(f"Error: Session file not found: {args.session}")
            sys.exit(1)


if __name__ == "__main__":
    main()