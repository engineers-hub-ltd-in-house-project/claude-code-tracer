#!/usr/bin/env python3
"""Database setup script for Claude Code Tracer."""

import argparse
import asyncio
import sys
from pathlib import Path

from supabase import Client, create_client

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.claude_code_tracer.utils.config import get_settings


async def create_tables(client: Client) -> None:
    """Create database tables."""
    
    # Create sessions table
    sessions_sql = """
    CREATE TABLE IF NOT EXISTS claude_sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id VARCHAR(255) UNIQUE NOT NULL,
        user_id UUID REFERENCES auth.users(id),
        project_path TEXT NOT NULL,
        start_time TIMESTAMPTZ NOT NULL,
        end_time TIMESTAMPTZ,
        total_interactions INTEGER DEFAULT 0,
        total_cost_usd DECIMAL(10,6) DEFAULT 0,
        status VARCHAR(50) DEFAULT 'active',
        metadata JSONB DEFAULT '{}',
        error_message TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ,
        
        CONSTRAINT check_status CHECK (status IN ('active', 'completed', 'error', 'timeout')),
        CONSTRAINT check_positive_interactions CHECK (total_interactions >= 0),
        CONSTRAINT check_positive_cost CHECK (total_cost_usd >= 0)
    );
    
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON claude_sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_status ON claude_sessions(status);
    CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON claude_sessions(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_sessions_project_path ON claude_sessions(project_path);
    """
    
    # Create interactions table
    interactions_sql = """
    CREATE TABLE IF NOT EXISTS claude_interactions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id UUID NOT NULL REFERENCES claude_sessions(id) ON DELETE CASCADE,
        message_type VARCHAR(50) NOT NULL,
        sequence_number INTEGER NOT NULL,
        user_prompt TEXT,
        claude_response TEXT,
        tools_used JSONB DEFAULT '[]',
        performance_metrics JSONB,
        context_analysis JSONB,
        privacy_status JSONB DEFAULT '{"scanned": false, "patterns_detected": [], "masking_applied": false}',
        error_message TEXT,
        raw_message JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        
        CONSTRAINT check_message_type CHECK (message_type IN ('user', 'assistant', 'system')),
        CONSTRAINT check_sequence_number CHECK (sequence_number >= 0),
        UNIQUE(session_id, sequence_number)
    );
    
    CREATE INDEX IF NOT EXISTS idx_interactions_session_id ON claude_interactions(session_id);
    CREATE INDEX IF NOT EXISTS idx_interactions_message_type ON claude_interactions(message_type);
    CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON claude_interactions(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_interactions_user_prompt ON claude_interactions USING gin(to_tsvector('english', user_prompt));
    CREATE INDEX IF NOT EXISTS idx_interactions_claude_response ON claude_interactions USING gin(to_tsvector('english', claude_response));
    """
    
    # Create analytics views
    analytics_sql = """
    CREATE OR REPLACE VIEW session_stats AS
    SELECT 
        COUNT(*) as total_sessions,
        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sessions,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as error_sessions,
        SUM(total_interactions) as total_interactions,
        SUM(total_cost_usd) as total_cost_usd,
        AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_session_duration_seconds,
        AVG(total_interactions) as avg_interactions_per_session
    FROM claude_sessions;
    
    CREATE OR REPLACE VIEW user_activity AS
    SELECT 
        user_id,
        COUNT(*) as session_count,
        SUM(total_interactions) as total_interactions,
        SUM(total_cost_usd) as total_cost_usd,
        MAX(created_at) as last_activity
    FROM claude_sessions
    WHERE user_id IS NOT NULL
    GROUP BY user_id;
    """
    
    # Execute SQL statements
    try:
        # Use admin client for DDL operations
        print("Creating sessions table...")
        client.postgrest.rpc("exec_sql", {"query": sessions_sql}).execute()
        
        print("Creating interactions table...")
        client.postgrest.rpc("exec_sql", {"query": interactions_sql}).execute()
        
        print("Creating analytics views...")
        client.postgrest.rpc("exec_sql", {"query": analytics_sql}).execute()
        
        print("✅ Database tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


async def create_rls_policies(client: Client) -> None:
    """Create Row Level Security policies."""
    
    policies_sql = """
    -- Enable RLS on tables
    ALTER TABLE claude_sessions ENABLE ROW LEVEL SECURITY;
    ALTER TABLE claude_interactions ENABLE ROW LEVEL SECURITY;
    
    -- Sessions policies
    CREATE POLICY "Users can view their own sessions" ON claude_sessions
        FOR SELECT USING (auth.uid() = user_id OR auth.uid() IS NULL);
    
    CREATE POLICY "Users can create their own sessions" ON claude_sessions
        FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);
    
    CREATE POLICY "Users can update their own sessions" ON claude_sessions
        FOR UPDATE USING (auth.uid() = user_id OR auth.uid() IS NULL);
    
    CREATE POLICY "Users can delete their own sessions" ON claude_sessions
        FOR DELETE USING (auth.uid() = user_id);
    
    -- Interactions policies (inherit from session ownership)
    CREATE POLICY "Users can view interactions from their sessions" ON claude_interactions
        FOR SELECT USING (
            session_id IN (
                SELECT id FROM claude_sessions WHERE auth.uid() = user_id OR auth.uid() IS NULL
            )
        );
    
    CREATE POLICY "Users can create interactions in their sessions" ON claude_interactions
        FOR INSERT WITH CHECK (
            session_id IN (
                SELECT id FROM claude_sessions WHERE auth.uid() = user_id OR user_id IS NULL
            )
        );
    
    CREATE POLICY "Users can update interactions in their sessions" ON claude_interactions
        FOR UPDATE USING (
            session_id IN (
                SELECT id FROM claude_sessions WHERE auth.uid() = user_id OR auth.uid() IS NULL
            )
        );
    
    CREATE POLICY "Users can delete interactions from their sessions" ON claude_interactions
        FOR DELETE USING (
            session_id IN (
                SELECT id FROM claude_sessions WHERE auth.uid() = user_id
            )
        );
    
    -- Service role bypass (for admin operations)
    CREATE POLICY "Service role has full access to sessions" ON claude_sessions
        FOR ALL USING (auth.role() = 'service_role');
    
    CREATE POLICY "Service role has full access to interactions" ON claude_interactions
        FOR ALL USING (auth.role() = 'service_role');
    """
    
    try:
        print("Setting up Row Level Security policies...")
        client.postgrest.rpc("exec_sql", {"query": policies_sql}).execute()
        print("✅ RLS policies created successfully!")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not create RLS policies: {e}")
        print("   This might be expected if policies already exist.")


async def create_functions(client: Client) -> None:
    """Create database functions and triggers."""
    
    functions_sql = """
    -- Function to update updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    -- Trigger for sessions table
    CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON claude_sessions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    -- Function to increment interaction count
    CREATE OR REPLACE FUNCTION increment_interaction_count()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE claude_sessions 
        SET total_interactions = total_interactions + 1
        WHERE id = NEW.session_id;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    -- Trigger for interaction count
    CREATE TRIGGER increment_session_interactions AFTER INSERT ON claude_interactions
        FOR EACH ROW EXECUTE FUNCTION increment_interaction_count();
    
    -- Function for full-text search
    CREATE OR REPLACE FUNCTION search_interactions(search_query TEXT, session_ids UUID[] DEFAULT NULL)
    RETURNS TABLE(
        id UUID,
        session_id UUID,
        message_type VARCHAR,
        user_prompt TEXT,
        claude_response TEXT,
        created_at TIMESTAMPTZ,
        rank REAL
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            i.id,
            i.session_id,
            i.message_type,
            i.user_prompt,
            i.claude_response,
            i.created_at,
            ts_rank(
                to_tsvector('english', COALESCE(i.user_prompt, '') || ' ' || COALESCE(i.claude_response, '')),
                plainto_tsquery('english', search_query)
            ) as rank
        FROM claude_interactions i
        WHERE (
            session_ids IS NULL OR i.session_id = ANY(session_ids)
        ) AND (
            to_tsvector('english', COALESCE(i.user_prompt, '') || ' ' || COALESCE(i.claude_response, ''))
            @@ plainto_tsquery('english', search_query)
        )
        ORDER BY rank DESC, i.created_at DESC;
    END;
    $$ language 'plpgsql';
    """
    
    try:
        print("Creating database functions and triggers...")
        client.postgrest.rpc("exec_sql", {"query": functions_sql}).execute()
        print("✅ Functions and triggers created successfully!")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not create functions: {e}")
        print("   This might be expected if functions already exist.")


async def create_storage_buckets(client: Client) -> None:
    """Create storage buckets for exports and backups."""
    
    buckets = [
        {
            "id": "exports",
            "name": "exports",
            "public": False,
            "file_size_limit": 52428800,  # 50MB
            "allowed_mime_types": ["application/json", "text/csv", "text/markdown"]
        },
        {
            "id": "backups",
            "name": "backups",
            "public": False,
            "file_size_limit": 104857600,  # 100MB
            "allowed_mime_types": ["application/json", "application/gzip"]
        }
    ]
    
    try:
        print("Creating storage buckets...")
        
        for bucket in buckets:
            try:
                client.storage.create_bucket(**bucket)
                print(f"  ✅ Created bucket: {bucket['name']}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"  ℹ️  Bucket already exists: {bucket['name']}")
                else:
                    raise
        
        print("✅ Storage buckets ready!")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not create storage buckets: {e}")


async def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup Claude Code Tracer database")
    parser.add_argument("--reset", action="store_true", help="Drop existing tables before creating")
    parser.add_argument("--skip-rls", action="store_true", help="Skip RLS policies creation")
    parser.add_argument("--skip-functions", action="store_true", help="Skip functions creation")
    parser.add_argument("--skip-storage", action="store_true", help="Skip storage buckets creation")
    args = parser.parse_args()
    
    print("🚀 Claude Code Tracer Database Setup")
    print("=" * 50)
    
    try:
        # Get settings and create admin client
        settings = get_settings()
        client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key.get_secret_value(),
        )
        
        print(f"📡 Connected to Supabase: {settings.supabase_url}")
        
        if args.reset:
            print("\n⚠️  RESETTING DATABASE - This will delete all data!")
            response = input("Are you sure? (yes/no): ")
            if response.lower() == "yes":
                drop_sql = """
                DROP TABLE IF EXISTS claude_interactions CASCADE;
                DROP TABLE IF EXISTS claude_sessions CASCADE;
                DROP VIEW IF EXISTS session_stats CASCADE;
                DROP VIEW IF EXISTS user_activity CASCADE;
                """
                client.postgrest.rpc("exec_sql", {"query": drop_sql}).execute()
                print("✅ Existing tables dropped!")
        
        # Create tables
        await create_tables(client)
        
        # Create RLS policies
        if not args.skip_rls:
            await create_rls_policies(client)
        
        # Create functions
        if not args.skip_functions:
            await create_functions(client)
        
        # Create storage buckets
        if not args.skip_storage:
            await create_storage_buckets(client)
        
        print("\n✨ Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and fill in your values")
        print("2. Run 'make dev' to start the development server")
        print("3. Run 'claude-tracer start' to begin monitoring")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())