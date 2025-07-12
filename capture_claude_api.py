#!/usr/bin/env python3
"""Capture and record Claude API interactions to Supabase."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import anthropic

sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_code_tracer.services.supabase import get_supabase_service
from claude_code_tracer.core.privacy import get_privacy_guard
from claude_code_tracer.models import SessionCreate, InteractionCreate
from claude_code_tracer.utils.config import get_settings


class ClaudeAPITracer:
    """Trace Claude API calls and record to Supabase."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_service()
        self.privacy_guard = get_privacy_guard()
        self.client = anthropic.Anthropic(
            api_key=self.settings.anthropic_api_key.get_secret_value()
        )
        self.current_session_id = None
        self.interaction_count = 0
    
    async def start_session(self, project_path: str = None):
        """Start a new tracking session."""
        if project_path is None:
            project_path = str(Path.cwd())
        
        session_data = SessionCreate(
            session_id=f"api-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            project_path=project_path,
            metadata={"source": "api", "model": "claude-3-sonnet"}
        )
        
        try:
            db_session = await self.supabase.create_session(session_data)
            self.current_session_id = db_session.id
            self.interaction_count = 0
            print(f"📝 Session started: {session_data.session_id}")
            return db_session
        except Exception as e:
            print(f"❌ Failed to create session: {e}")
            return None
    
    async def send_message(self, prompt: str, system: str = None) -> str:
        """Send message to Claude and record the interaction."""
        if not self.current_session_id:
            await self.start_session()
        
        # Apply privacy protection to prompt
        masked_prompt, privacy_matches = self.privacy_guard.mask_text(prompt)
        
        # Create interaction record for user message
        interaction = InteractionCreate(
            session_id=self.current_session_id,
            message_type="user",
            sequence_number=self.interaction_count,
            user_prompt=masked_prompt,
            privacy_status={
                "scanned": True,
                "patterns_detected": [m.pattern_name for m in privacy_matches],
                "masking_applied": len(privacy_matches) > 0,
                "scan_timestamp": datetime.utcnow(),
            }
        )
        
        try:
            # Send to Claude API
            messages = [{"role": "user", "content": prompt}]
            if system:
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1024,
                    system=system,
                    messages=messages
                )
            else:
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1024,
                    messages=messages
                )
            
            # Extract response text
            response_text = response.content[0].text if response.content else ""
            
            # Apply privacy protection to response
            masked_response, _ = self.privacy_guard.mask_text(response_text)
            
            # Update interaction with response
            interaction.claude_response = masked_response
            interaction.performance_metrics = {
                "response_time_ms": 0,  # Not available from API
                "tokens_used": {
                    "prompt": response.usage.input_tokens,
                    "completion": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": response.model,
                "cost_usd": self._calculate_cost(response.usage)
            }
            
            # Save to Supabase
            await self.supabase.create_interaction(interaction)
            self.interaction_count += 1
            
            print(f"💬 Interaction {self.interaction_count} recorded")
            print(f"   Tokens: {response.usage.input_tokens} + {response.usage.output_tokens}")
            print(f"   Cost: ${interaction.performance_metrics['cost_usd']:.4f}")
            
            return response_text
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return f"Error: {str(e)}"
    
    def _calculate_cost(self, usage) -> float:
        """Calculate cost based on token usage."""
        # Claude 3 Sonnet pricing (approximate)
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015
        
        input_cost = (usage.input_tokens / 1000) * input_cost_per_1k
        output_cost = (usage.output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
    
    async def end_session(self):
        """End the current session."""
        if self.current_session_id:
            from claude_code_tracer.models import SessionUpdate
            
            update = SessionUpdate(
                status="completed",
                end_time=datetime.utcnow(),
                total_interactions=self.interaction_count
            )
            
            await self.supabase.update_session(self.current_session_id, update)
            print(f"✅ Session ended: {self.interaction_count} interactions")
            
            self.current_session_id = None
            self.interaction_count = 0


async def interactive_demo():
    """Interactive demo with Claude API."""
    tracer = ClaudeAPITracer()
    
    print("🤖 Claude API Tracer - Interactive Demo")
    print("=" * 50)
    print("Type 'exit' to quit, 'new' for new session")
    print()
    
    await tracer.start_session()
    
    while True:
        try:
            prompt = input("\n👤 You: ").strip()
            
            if prompt.lower() == 'exit':
                await tracer.end_session()
                break
            elif prompt.lower() == 'new':
                await tracer.end_session()
                await tracer.start_session()
                continue
            elif not prompt:
                continue
            
            print("\n🤖 Claude: ", end="", flush=True)
            response = await tracer.send_message(prompt)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            await tracer.end_session()
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude API Tracer")
    parser.add_argument("--demo", action="store_true", help="Run interactive demo")
    parser.add_argument("--prompt", type=str, help="Single prompt to send")
    args = parser.parse_args()
    
    if args.demo:
        await interactive_demo()
    elif args.prompt:
        tracer = ClaudeAPITracer()
        await tracer.start_session()
        response = await tracer.send_message(args.prompt)
        print(f"\n🤖 Claude: {response}")
        await tracer.end_session()
    else:
        print("Usage:")
        print("  python capture_claude_api.py --demo     # Interactive mode")
        print("  python capture_claude_api.py --prompt 'Your question'")


if __name__ == "__main__":
    asyncio.run(main())