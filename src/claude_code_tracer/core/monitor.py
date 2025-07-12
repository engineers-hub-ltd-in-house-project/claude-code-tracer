"""
Claude Code session monitoring and data collection
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

from claude_code_sdk import query, ClaudeCodeOptions, SDKMessage

from ..models.interaction import InteractionCreate
from ..models.session import SessionCreate
from ..services.supabase_client import SupabaseService
from ..utils.config import get_settings
from .privacy import PrivacyGuard

logger = logging.getLogger(__name__)


class ClaudeCodeMonitor:
    """Monitor and collect Claude Code session data"""
    
    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.settings = get_settings()
        self.supabase = supabase_service or SupabaseService()
        self.privacy_guard = PrivacyGuard()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
    async def start_monitoring(self):
        """Start continuous monitoring of Claude Code sessions"""
        logger.info("Starting Claude Code monitoring...")
        
        while True:
            try:
                await self._check_active_sessions()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(10)
                
    async def _check_active_sessions(self):
        """Check for active Claude Code sessions"""
        try:
            # Use Claude Code SDK to check for sessions
            async for message in query(
                prompt="",  # Empty prompt for status check
                options=ClaudeCodeOptions(
                    max_turns=0,
                    permission_mode="default"
                )
            ):
                if isinstance(message, dict) and message.get("type") == "system":
                    await self._handle_system_message(message)
                    
        except Exception as e:
            logger.debug(f"Session check: {e}")
    
    async def _handle_system_message(self, message: Dict[str, Any]):
        """Handle system messages from Claude Code"""
        if message.get("subtype") == "init":
            session_id = message.get("session_id")
            if session_id and session_id not in self.active_sessions:
                await self._register_new_session(message)
                
    async def _register_new_session(self, system_message: Dict[str, Any]):
        """Register a new Claude Code session"""
        session_id = system_message["session_id"]
        
        session_data = SessionCreate(
            session_id=session_id,
            project_path=system_message.get("cwd", ""),
            metadata={
                "tools": system_message.get("tools", []),
                "model": system_message.get("model", "unknown"),
                "api_key_source": system_message.get("apiKeySource", "")
            }
        )
        
        self.active_sessions[session_id] = {
            "start_time": datetime.now(),
            "data": session_data
        }
        
        # Save to Supabase
        try:
            await self.supabase.create_session(session_data.dict())
            logger.info(f"New session registered: {session_id}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
        
        # Start monitoring this specific session
        asyncio.create_task(self._monitor_session(session_id))
        
    async def _monitor_session(self, session_id: str):
        """Monitor a specific Claude Code session"""
        logger.info(f"Monitoring session: {session_id}")
        
        try:
            async for message in query(
                prompt="",
                options=ClaudeCodeOptions(
                    max_turns=100,  # Monitor for extended period
                    permission_mode="default"
                )
            ):
                if isinstance(message, dict):
                    await self._process_session_message(session_id, message)
                    
        except Exception as e:
            logger.error(f"Session {session_id} monitoring error: {e}")
            await self._handle_session_end(session_id)
            
    async def _process_session_message(self, session_id: str, message: Dict[str, Any]):
        """Process messages from a Claude Code session"""
        message_type = message.get("type")
        
        if message_type in ["user", "assistant"]:
            interaction = InteractionCreate(
                session_id=session_id,
                message_type=message_type,
                timestamp=datetime.now()
            )
            
            if message_type == "user":
                content = message.get("message", {}).get("content", "")
                # Apply privacy protection
                masked_content, detected_patterns = self.privacy_guard.scan_and_mask(content)
                interaction.user_prompt = masked_content
                interaction.privacy_status = {
                    "contains_sensitive": len(detected_patterns) > 0,
                    "detected_patterns": detected_patterns
                }
                
            elif message_type == "assistant":
                interaction.claude_response = json.dumps(message.get("message", {}))
                
                # Extract tools used
                assistant_message = message.get("message", {})
                if isinstance(assistant_message.get("content"), list):
                    tools = [
                        item.get("name") 
                        for item in assistant_message["content"] 
                        if item.get("type") == "tool_use"
                    ]
                    interaction.tools_used = tools
            
            # Save interaction
            try:
                await self.supabase.create_interaction(interaction.dict())
            except Exception as e:
                logger.error(f"Failed to save interaction: {e}")
                
        elif message_type == "result":
            await self._handle_session_result(session_id, message)
            
    async def _handle_session_result(self, session_id: str, result_message: Dict[str, Any]):
        """Handle session completion"""
        if session_id in self.active_sessions:
            session_update = {
                "end_time": datetime.now(),
                "total_cost_usd": result_message.get("total_cost_usd", 0),
                "num_turns": result_message.get("num_turns", 0),
                "duration_ms": result_message.get("duration_ms", 0),
                "status": "completed" if not result_message.get("is_error") else "error"
            }
            
            try:
                await self.supabase.update_session(session_id, session_update)
                logger.info(f"Session completed: {session_id}")
            except Exception as e:
                logger.error(f"Failed to update session: {e}")
            
            del self.active_sessions[session_id]
            
    async def _handle_session_end(self, session_id: str):
        """Handle unexpected session termination"""
        if session_id in self.active_sessions:
            try:
                await self.supabase.update_session(session_id, {
                    "end_time": datetime.now(),
                    "status": "timeout"
                })
            except Exception as e:
                logger.error(f"Failed to mark session as ended: {e}")
                
            del self.active_sessions[session_id]


async def start_monitoring():
    """Entry point for starting the monitoring service"""
    monitor = ClaudeCodeMonitor()
    await monitor.start_monitoring()