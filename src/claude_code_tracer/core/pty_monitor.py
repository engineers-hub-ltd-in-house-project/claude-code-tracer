"""PTY-based monitoring for Claude CLI sessions."""

import os
import pty
import select
import subprocess
import sys
import termios
import tty
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import json
import re

from claude_code_tracer.models import SessionCreate, InteractionCreate
from claude_code_tracer.core.privacy import get_privacy_guard
from claude_code_tracer.utils.config import get_settings


class PTYMonitor:
    """Monitor Claude CLI using pseudo-terminal."""
    
    def __init__(self, debug=False):
        """Initialize PTY monitor."""
        self.settings = get_settings()
        self.privacy_guard = get_privacy_guard()
        self.sessions_dir = Path("./sessions")
        self.sessions_dir.mkdir(exist_ok=True)
        self.debug = debug
        
        # Session tracking
        self.current_session = None
        self.session_file = None
        self.interaction_buffer = {"user": "", "assistant": ""}
        self.interaction_count = 0
        self.capture_mode = "waiting"  # waiting, user_input, assistant_output
        
        # Debug logging
        self.debug_file = None
        if debug:
            self.debug_file = self.sessions_dir / f"debug-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    
    def _strip_ansi(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        # Pattern to match ANSI escape sequences
        ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07|\x1b[PX^_].*?\x1b\\|\x1b\[\?[0-9]+[hl]')
        return ansi_escape.sub('', text)
    
    def _clean_claude_output(self, text: str) -> str:
        """Clean Claude CLI decorative elements."""
        # Remove box drawing characters
        text = re.sub(r'[╭─╮│╰╯┐└┘├┤┬┴┼]', '', text)
        
        # Remove bullet points and arrows
        text = re.sub(r'[⎿⧉✻●•▸▹⬤]', '', text)
        
        # Remove extra spaces and normalize
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'^\s*\n', '', text, flags=re.MULTILINE)
        
        # Remove common UI patterns
        text = re.sub(r'Welcome to Claude Code!', '', text)
        text = re.sub(r'/help for help.*', '', text)
        text = re.sub(r'cwd:.*', '', text)
        text = re.sub(r'\(\d+s.*tokens.*\)', '', text)
        text = re.sub(r'Selected \d+ lines from.*', '', text)
        
        return text.strip()
    
    def _debug_log(self, message: str):
        """Write debug message to file instead of stdout."""
        if self.debug and self.debug_file:
            with open(self.debug_file, "a") as f:
                f.write(f"{datetime.now().isoformat()} {message}\n")
    
    def start_monitoring(self, command: str = "claude"):
        """Start monitoring Claude CLI session."""
        # Create session
        session_id = f"pty-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.current_session = {
            "id": session_id,
            "session_id": session_id,
            "project_path": str(Path.cwd()),
            "start_time": datetime.utcnow().isoformat(),
            "status": "active",
            "interactions": [],
            "metadata": {
                "monitor_type": "pty",
                "command": command
            }
        }
        
        self.session_file = self.sessions_dir / f"{session_id}.json"
        self._save_session()
        
        print(f"🚀 Claude Code Tracer - PTY Monitor")
        print(f"=" * 50)
        print(f"📝 Session ID: {session_id}")
        print(f"📁 Logs saved to: {self.session_file}")
        if self.debug:
            print(f"🐛 Debug logs: {self.debug_file}")
        print(f"=" * 50)
        print(f"Starting {command}...\n")
        
        # Save terminal settings
        old_tty = termios.tcgetattr(sys.stdin)
        
        try:
            # Create PTY
            master_fd, slave_fd = pty.openpty()
            
            # Start Claude CLI process
            process = subprocess.Popen(
                [command],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                preexec_fn=os.setsid
            )
            
            os.close(slave_fd)
            
            # Set stdin to raw mode
            tty.setraw(sys.stdin.fileno())
            
            # Monitor loop
            self._monitor_loop(master_fd, process)
            
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
            
            # Complete session
            self._complete_session()
    
    def _monitor_loop(self, master_fd: int, process: subprocess.Popen):
        """Main monitoring loop."""
        output_buffer = ""
        
        while True:
            try:
                # Check if process is still running
                if process.poll() is not None:
                    break
                
                # Wait for input from stdin or master_fd
                r, w, e = select.select([sys.stdin, master_fd], [], [], 0.1)
                
                if sys.stdin in r:
                    # User input
                    data = os.read(sys.stdin.fileno(), 1024)
                    if not data:
                        break
                    
                    # Check for Ctrl+D (EOF)
                    if data == b'\x04':
                        break
                    
                    # Write to PTY
                    os.write(master_fd, data)
                    
                    # Capture user input
                    try:
                        text = data.decode('utf-8', errors='ignore')
                        self._capture_input(text)
                    except Exception as e:
                        self._debug_log(f"[ERROR] Input decode: {e}")
                
                if master_fd in r:
                    # Output from Claude
                    data = os.read(master_fd, 1024)
                    if not data:
                        break
                    
                    # Write to stdout
                    os.write(sys.stdout.fileno(), data)
                    
                    # Capture output
                    try:
                        text = data.decode('utf-8', errors='ignore')
                        output_buffer += text
                        
                        # Process complete lines or when we see a prompt
                        if '\n' in text or '>' in text:
                            self._process_output_buffer(output_buffer)
                            if '>' in text:
                                output_buffer = ""
                            else:
                                # Keep incomplete lines in buffer
                                lines = output_buffer.split('\n')
                                output_buffer = lines[-1]
                    except Exception as e:
                        self._debug_log(f"[ERROR] Output decode: {e}")
                    
            except (OSError, IOError) as e:
                self._debug_log(f"[ERROR] Loop error: {e}")
                break
    
    def _capture_input(self, text: str):
        """Capture user input."""
        self._debug_log(f"[INPUT] Raw: {repr(text)}")
        
        # Check for Enter key
        if '\r' in text or '\n' in text:
            # User pressed Enter, switch to capturing assistant output
            self.capture_mode = "assistant_output"
            clean_input = self._strip_ansi(self.interaction_buffer["user"] + text)
            self._debug_log(f"[INPUT] Complete: {repr(clean_input)}")
        else:
            # Still typing
            if self.capture_mode == "waiting":
                self.capture_mode = "user_input"
                self._debug_log("[STATE] Switched to user_input mode")
            
            if self.capture_mode == "user_input":
                self.interaction_buffer["user"] += text
    
    def _process_output_buffer(self, buffer: str):
        """Process output buffer to detect Claude responses."""
        clean_buffer = self._strip_ansi(buffer)
        self._debug_log(f"[OUTPUT] Buffer: {repr(clean_buffer[:100])}...")
        
        # Look for Claude's response pattern
        lines = clean_buffer.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and prompts
            if not line or line == '>':
                continue
            
            # If we're in assistant output mode, capture the response
            if self.capture_mode == "assistant_output":
                # Skip echo of user input (Claude sometimes echoes the command)
                user_clean = self._strip_ansi(self.interaction_buffer["user"]).strip()
                if line == user_clean:
                    continue
                
                # This is Claude's response
                self.interaction_buffer["assistant"] += line + "\n"
                self._debug_log(f"[CAPTURE] Assistant: {repr(line)}")
        
        # Check if we're back at prompt
        if '>' in clean_buffer and self.capture_mode == "assistant_output":
            # Save the interaction
            self._save_interaction()
            self.capture_mode = "waiting"
            self._debug_log("[STATE] Back to waiting mode")
    
    def _save_interaction(self):
        """Save the current interaction."""
        # Clean up the buffers
        user_input = self._strip_ansi(self.interaction_buffer["user"]).strip()
        assistant_output = self._strip_ansi(self.interaction_buffer["assistant"]).strip()
        
        self._debug_log(f"[SAVE] User: {repr(user_input[:50])}...")
        self._debug_log(f"[SAVE] Assistant: {repr(assistant_output[:50])}...")
        
        if not user_input:
            self._debug_log("[SAVE] Skipping - no user input")
            return
        
        # Clean Claude UI elements
        clean_input = self._clean_claude_output(user_input)
        clean_output = self._clean_claude_output(assistant_output)
        
        # Apply privacy protection
        masked_input, _ = self.privacy_guard.mask_text(clean_input)
        masked_output, _ = self.privacy_guard.mask_text(clean_output) if clean_output else ("", [])
        
        # Create interaction
        interaction = {
            "id": f"int-{self.interaction_count}",
            "sequence_number": self.interaction_count,
            "timestamp": datetime.utcnow().isoformat(),
            "user_prompt": masked_input,
            "claude_response": masked_output,
            "message_type": "interaction",
            "raw_user": user_input,  # Keep raw for debugging
            "raw_assistant": assistant_output
        }
        
        # Add to session
        self.current_session["interactions"].append(interaction)
        self.interaction_count += 1
        
        # Save to file
        self._save_session()
        self._debug_log(f"[SAVE] Interaction {self.interaction_count} saved")
        
        # Clear buffers
        self.interaction_buffer = {"user": "", "assistant": ""}
    
    def _save_session(self):
        """Save session to file."""
        if self.session_file and self.current_session:
            with open(self.session_file, "w") as f:
                json.dump(self.current_session, f, indent=2)
    
    def _complete_session(self):
        """Complete the current session."""
        if self.current_session:
            self.current_session["end_time"] = datetime.utcnow().isoformat()
            self.current_session["status"] = "completed"
            self.current_session["total_interactions"] = self.interaction_count
            self._save_session()
            
            print(f"\n\n✅ Session completed: {self.current_session['id']}")
            print(f"📊 Total interactions: {self.interaction_count}")
            print(f"💾 Saved to: {self.session_file}")
            if self.debug and self.debug_file:
                print(f"🐛 Debug log: {self.debug_file}")