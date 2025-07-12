-- Migration: 001_initial_schema
-- Created: 2024-01-12
-- Description: Initial database schema for Claude Code Tracer

-- This migration creates the initial tables and relationships
-- Run this after setting up Supabase Auth

BEGIN;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User profiles table
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions table
CREATE TABLE claude_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    project_path TEXT,
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    total_interactions INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,6) DEFAULT 0.000000,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT status_check CHECK (status IN ('active', 'completed', 'error', 'timeout'))
);

-- Interactions table
CREATE TABLE claude_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES claude_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(50) NOT NULL,
    user_prompt TEXT,
    claude_response TEXT,
    tools_used JSONB DEFAULT '[]',
    files_affected JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    context_analysis JSONB DEFAULT '{}',
    privacy_status JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT message_type_check CHECK (message_type IN ('user', 'assistant', 'system', 'result'))
);

-- Create indexes
CREATE INDEX idx_sessions_user_id ON claude_sessions(user_id);
CREATE INDEX idx_sessions_status ON claude_sessions(status);
CREATE INDEX idx_sessions_start_time ON claude_sessions(start_time DESC);
CREATE INDEX idx_interactions_session_id ON claude_interactions(session_id);
CREATE INDEX idx_interactions_created_at ON claude_interactions(created_at DESC);

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE claude_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE claude_interactions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own sessions" ON claude_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own sessions" ON claude_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON claude_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions" ON claude_sessions
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own interactions" ON claude_interactions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM claude_sessions 
            WHERE claude_sessions.id = claude_interactions.session_id 
            AND claude_sessions.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create interactions for own sessions" ON claude_interactions
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM claude_sessions 
            WHERE claude_sessions.id = claude_interactions.session_id 
            AND claude_sessions.user_id = auth.uid()
        )
    );

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update timestamp triggers
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claude_sessions_updated_at BEFORE UPDATE ON claude_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;