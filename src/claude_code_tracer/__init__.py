"""
Claude Code Tracer - Track and analyze Claude Code interactions

A comprehensive system for monitoring, recording, and analyzing interactions
with Claude Code to improve development efficiency and knowledge sharing.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.monitor import ClaudeCodeMonitor
from .core.privacy import PrivacyGuard
from .services.supabase_client import SupabaseService

__all__ = [
    "ClaudeCodeMonitor",
    "PrivacyGuard",
    "SupabaseService",
]