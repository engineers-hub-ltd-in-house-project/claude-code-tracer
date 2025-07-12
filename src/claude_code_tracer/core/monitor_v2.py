"""Updated monitoring module for Claude Code sessions using real SDK."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import anyio
from claude_code_sdk import query, ClaudeCodeOptions
from claude_code_sdk.types import (
    UserMessage, 
    AssistantMessage, 
    SystemMessage, 
    ResultMessage,
    ToolUseBlock,
    ToolResultBlock,
    TextBlock
)

from claude_code_tracer.core.privacy import get_privacy_guard
from claude_code_tracer.models import (
    ContextAnalysis,
    InteractionCreate,
    PerformanceMetrics,
    PrivacyStatus,
    SessionCreate,
    SessionUpdate,
    ToolUsage,
)
from claude_code_tracer.services.supabase import get_supabase_service
from claude_code_tracer.utils.config import get_settings
import json as json_module


class ClaudeCodeMonitorV2:
    """Monitor for real Claude Code SDK sessions."""
    
    def __init__(self):
        """Initialize the monitor with required services."""
        self.settings = get_settings()
        self.privacy_guard = get_privacy_guard()
        
        # Check if using demo/local mode
        self.use_local_storage = self.settings.supabase_url == "https://demo-project.supabase.co"
        if not self.use_local_storage:
            try:
                self.supabase = get_supabase_service()
            except:
                print("⚠️  Supabase connection failed, using local storage")
                self.use_local_storage = True
        
        # Active sessions tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.interaction_counters: Dict[str, int] = {}
        
        # Local storage directory
        if self.use_local_storage:
            self.sessions_dir = Path("./sessions")
            self.sessions_dir.mkdir(exist_ok=True)
    
    async def monitor_query(
        self, 
        prompt: str, 
        options: Optional[ClaudeCodeOptions] = None,
        session_id: Optional[str] = None
    ):
        """Monitor a Claude Code query and record interactions."""
        # Generate or use provided session ID
        if not session_id:
            session_id = f"session-{hashlib.md5(f'{prompt}-{datetime.now()}'.encode()).hexdigest()[:8]}"
        
        # Create session if new
        if session_id not in self.active_sessions:
            await self._create_session(session_id, options)
            
        # Check if session was created successfully
        if session_id not in self.active_sessions:
            print(f"❌ Failed to create session {session_id}")
            return
        
        # Apply privacy protection to prompt
        masked_prompt, privacy_matches = self.privacy_guard.mask_text(prompt)
        
        # Track interaction count
        interaction_num = self.interaction_counters.get(session_id, 0)
        
        # Create user interaction
        user_interaction = InteractionCreate(
            session_id=self.active_sessions[session_id]["db_id"],
            message_type="user",
            sequence_number=interaction_num,
            user_prompt=masked_prompt,
            privacy_status=PrivacyStatus(
                scanned=True,
                patterns_detected=[m.pattern_name for m in privacy_matches],
                masking_applied=len(privacy_matches) > 0,
                scan_timestamp=datetime.utcnow(),
            ),
        )
        
        # Save user message
        if self.use_local_storage:
            await self._save_local_interaction(session_id, user_interaction)
        else:
            await self.supabase.create_interaction(user_interaction)
        self.interaction_counters[session_id] += 1
        
        print(f"📝 Session: {session_id}")
        print(f"👤 User: {prompt[:50]}...")
        
        # Collect assistant response and tools
        assistant_text = ""
        tools_used = []
        
        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, UserMessage):
                    # Already handled above
                    pass
                    
                elif isinstance(message, AssistantMessage):
                    # Extract text and tool usage
                    for content in message.content:
                        if isinstance(content, TextBlock):
                            assistant_text += content.text
                        elif isinstance(content, ToolUseBlock):
                            tools_used.append(ToolUsage(
                                tool_name=content.tool,
                                parameters=content.args,
                                execution_time_ms=0,  # Not available
                            ))
                            print(f"   🔧 Tool: {content.tool}")
                
                elif isinstance(message, ResultMessage):
                    # Tool result
                    if tools_used:
                        tools_used[-1].result_summary = str(message.content)[:100]
                
                elif isinstance(message, SystemMessage):
                    # System messages
                    print(f"   ℹ️  System: {message.content}")
            
            # Apply privacy protection to response
            masked_response, _ = self.privacy_guard.mask_text(assistant_text)
            
            # Create assistant interaction
            assistant_interaction = InteractionCreate(
                session_id=self.active_sessions[session_id]["db_id"],
                message_type="assistant",
                sequence_number=self.interaction_counters[session_id],
                claude_response=masked_response,
                tools_used=tools_used,
                context_analysis=self._analyze_context(masked_prompt, masked_response),
            )
            
            # Save assistant response
            if self.use_local_storage:
                await self._save_local_interaction(session_id, assistant_interaction)
            else:
                await self.supabase.create_interaction(assistant_interaction)
            self.interaction_counters[session_id] += 1
            
            print(f"🤖 Claude: {assistant_text[:50]}...")
            print(f"   Tools used: {len(tools_used)}")
            
        except Exception as e:
            print(f"❌ Error during query: {e}")
            await self._complete_session(session_id, status="error", error_message=str(e))
    
    async def _create_session(self, session_id: str, options: Optional[ClaudeCodeOptions]):
        """Create a new session in the database or locally."""
        session_data = SessionCreate(
            session_id=session_id,
            project_path=str(options.cwd if options and options.cwd else Path.cwd()),
            metadata={
                "sdk_version": "real",
                "system_prompt": options.system_prompt if options else None,
            },
        )
        
        try:
            if self.use_local_storage:
                # Save to local file
                session_file = self.sessions_dir / f"{session_id}.json"
                session_dict = session_data.model_dump(mode='json')
                session_dict["id"] = str(uuid4())
                session_dict["interactions"] = []
                
                with open(session_file, "w") as f:
                    json_module.dump(session_dict, f, indent=2)
                
                self.active_sessions[session_id] = {
                    "db_id": session_dict["id"],
                    "start_time": datetime.utcnow(),
                    "total_cost": 0.0,
                    "file_path": session_file,
                }
            else:
                db_session = await self.supabase.create_session(session_data)
                
                self.active_sessions[session_id] = {
                    "db_id": db_session.id,
                    "start_time": datetime.utcnow(),
                    "total_cost": 0.0,
                }
            
            self.interaction_counters[session_id] = 0
            print(f"✅ Session created: {session_id}")
        
        except Exception as e:
            print(f"❌ Failed to create session: {e}")
    
    async def _complete_session(
        self,
        session_id: str,
        status: str = "completed",
        error_message: Optional[str] = None,
    ):
        """Complete a session and update database."""
        if session_id not in self.active_sessions:
            return
        
        session_data = self.active_sessions[session_id]
        
        update_data = SessionUpdate(
            status=status,
            end_time=datetime.utcnow(),
            total_interactions=self.interaction_counters.get(session_id, 0),
            total_cost_usd=session_data["total_cost"],
            error_message=error_message,
        )
        
        try:
            if self.use_local_storage:
                # Update local file
                session_file = session_data.get("file_path")
                if session_file and session_file.exists():
                    with open(session_file, "r") as f:
                        data = json_module.load(f)
                    
                    data.update(update_data.model_dump(exclude_unset=True))
                    data["end_time"] = datetime.utcnow().isoformat()
                    
                    with open(session_file, "w") as f:
                        json_module.dump(data, f, indent=2)
            else:
                await self.supabase.update_session(
                    session_data["db_id"],
                    update_data,
                )
            
            self.active_sessions.pop(session_id, None)
            self.interaction_counters.pop(session_id, None)
            
            print(f"✅ Session completed: {session_id}")
        
        except Exception as e:
            print(f"❌ Failed to complete session: {e}")
    
    def _analyze_context(self, user_prompt: str, assistant_response: str) -> ContextAnalysis:
        """Analyze interaction context for insights."""
        combined_text = f"{user_prompt}\n{assistant_response}".lower()
        
        # Detect intent type
        intent_type = "general"
        if any(word in combined_text for word in ["fix", "bug", "error", "issue"]):
            intent_type = "debugging"
        elif any(word in combined_text for word in ["create", "implement", "add", "new"]):
            intent_type = "code_generation"
        elif any(word in combined_text for word in ["refactor", "improve", "optimize"]):
            intent_type = "refactoring"
        elif any(word in combined_text for word in ["test", "testing", "unittest"]):
            intent_type = "testing"
        elif any(word in combined_text for word in ["explain", "understand", "what", "how"]):
            intent_type = "explanation"
        
        # Detect programming languages
        languages = []
        lang_keywords = {
            "python": ["def ", "import ", "self.", "pip", ".py"],
            "javascript": ["const ", "let ", "var ", "function ", ".js"],
            "typescript": ["interface ", "type ", ": string", ": number", ".ts"],
        }
        
        for lang, keywords in lang_keywords.items():
            if any(kw in combined_text for kw in keywords):
                languages.append(lang)
        
        return ContextAnalysis(
            intent_type=intent_type,
            programming_languages=languages[:3],
            frameworks=[],
            complexity_score=min(1.0, len(combined_text) / 5000),
            topics=[],
        )
    
    async def _save_local_interaction(self, session_id: str, interaction: InteractionCreate):
        """Save interaction to local session file."""
        session_data = self.active_sessions.get(session_id)
        if not session_data or "file_path" not in session_data:
            return
        
        session_file = session_data["file_path"]
        if session_file.exists():
            with open(session_file, "r") as f:
                data = json_module.load(f)
            
            interaction_dict = interaction.model_dump(mode='json')
            interaction_dict["id"] = str(uuid4())
            data["interactions"].append(interaction_dict)
            
            with open(session_file, "w") as f:
                json_module.dump(data, f, indent=2)


async def demo_real_sdk():
    """Demo using the real Claude Code SDK."""
    print("🚀 Claude Code Tracer - Real SDK Demo")
    print("=" * 50)
    
    monitor = ClaudeCodeMonitorV2()
    
    # Simple query
    print("\n📝 Test 1: Simple calculation")
    await monitor.monitor_query("What is 2 + 2?")
    
    # Query with tools
    print("\n📝 Test 2: File operation")
    options = ClaudeCodeOptions(
        system_prompt="You are a helpful coding assistant",
        permission_mode='acceptEdits'
    )
    
    await monitor.monitor_query(
        "Create a simple hello.py file that prints 'Hello from Claude Code!'",
        options=options
    )
    
    # Complete sessions
    for session_id in list(monitor.active_sessions.keys()):
        await monitor._complete_session(session_id)
    
    print("\n✨ Demo complete!")


if __name__ == "__main__":
    anyio.run(demo_real_sdk)