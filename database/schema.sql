-- Claude Code Tracer Database Schema
-- Supabase (PostgreSQL) compatible

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable Row Level Security
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret';

-- ========================================
-- User Management (extends Supabase Auth)
-- ========================================

-- User profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========================================
-- Sessions Table
-- ========================================

CREATE TABLE IF NOT EXISTS claude_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    project_path TEXT,
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    total_interactions INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,6) DEFAULT 0.000000,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'error', 'timeout')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for sessions
CREATE INDEX idx_sessions_user_id ON claude_sessions(user_id);
CREATE INDEX idx_sessions_status ON claude_sessions(status);
CREATE INDEX idx_sessions_start_time ON claude_sessions(start_time DESC);
CREATE INDEX idx_sessions_project_path ON claude_sessions(project_path);

-- ========================================
-- Interactions Table
-- ========================================

CREATE TABLE IF NOT EXISTS claude_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES claude_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(50) NOT NULL CHECK (message_type IN ('user', 'assistant', 'system', 'result')),
    user_prompt TEXT,
    claude_response TEXT,
    tools_used JSONB DEFAULT '[]',
    files_affected JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    context_analysis JSONB DEFAULT '{}',
    privacy_status JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for interactions
CREATE INDEX idx_interactions_session_id ON claude_interactions(session_id);
CREATE INDEX idx_interactions_created_at ON claude_interactions(created_at DESC);
CREATE INDEX idx_interactions_message_type ON claude_interactions(message_type);
CREATE INDEX idx_interactions_tools_used ON claude_interactions USING GIN (tools_used);

-- ========================================
-- Analytics Tables
-- ========================================

-- Daily aggregated statistics
CREATE TABLE IF NOT EXISTS daily_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    total_interactions INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,6) DEFAULT 0.000000,
    avg_session_duration_seconds INTEGER,
    success_rate DECIMAL(5,4),
    top_operations JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

CREATE INDEX idx_daily_stats_user_date ON daily_statistics(user_id, date DESC);

-- Project analytics
CREATE TABLE IF NOT EXISTS project_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    project_path TEXT NOT NULL,
    analysis_date DATE NOT NULL,
    interaction_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4),
    avg_response_time_ms DECIMAL(10,2),
    total_cost_usd DECIMAL(10,6) DEFAULT 0.000000,
    top_operations JSONB DEFAULT '[]',
    insights JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, project_path, analysis_date)
);

CREATE INDEX idx_project_analytics_user_project ON project_analytics(user_id, project_path);

-- ========================================
-- Privacy & Security Tables
-- ========================================

-- Privacy patterns
CREATE TABLE IF NOT EXISTS privacy_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    pattern_name VARCHAR(255) NOT NULL,
    pattern_regex TEXT NOT NULL,
    replacement TEXT NOT NULL,
    severity_level INTEGER CHECK (severity_level BETWEEN 1 AND 5),
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- ========================================
-- Export & Backup Tables
-- ========================================

CREATE TABLE IF NOT EXISTS export_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    export_type VARCHAR(50) NOT NULL CHECK (export_type IN ('json', 'csv', 'markdown')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    filters JSONB DEFAULT '{}',
    file_url TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ
);

-- ========================================
-- Row Level Security (RLS) Policies
-- ========================================

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE claude_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE claude_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE privacy_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE export_jobs ENABLE ROW LEVEL SECURITY;

-- User profiles policies
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- Sessions policies
CREATE POLICY "Users can view own sessions" ON claude_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own sessions" ON claude_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON claude_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions" ON claude_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Interactions policies
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

-- Analytics policies
CREATE POLICY "Users can view own statistics" ON daily_statistics
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own project analytics" ON project_analytics
    FOR SELECT USING (auth.uid() = user_id);

-- Privacy patterns policies
CREATE POLICY "Users can manage own privacy patterns" ON privacy_patterns
    FOR ALL USING (auth.uid() = user_id);

-- Audit logs policies
CREATE POLICY "Users can view own audit logs" ON audit_logs
    FOR SELECT USING (auth.uid() = user_id);

-- Export jobs policies
CREATE POLICY "Users can manage own export jobs" ON export_jobs
    FOR ALL USING (auth.uid() = user_id);

-- ========================================
-- Functions and Triggers
-- ========================================

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

CREATE TRIGGER update_privacy_patterns_updated_at BEFORE UPDATE ON privacy_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate session statistics
CREATE OR REPLACE FUNCTION calculate_session_statistics(session_uuid UUID)
RETURNS TABLE (
    interaction_count INTEGER,
    duration_seconds INTEGER,
    tools_used_count INTEGER,
    files_affected_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as interaction_count,
        EXTRACT(EPOCH FROM (
            COALESCE(s.end_time, NOW()) - s.start_time
        ))::INTEGER as duration_seconds,
        COUNT(DISTINCT jsonb_array_elements_text(i.tools_used))::INTEGER as tools_used_count,
        COUNT(DISTINCT jsonb_array_elements_text(i.files_affected))::INTEGER as files_affected_count
    FROM claude_sessions s
    LEFT JOIN claude_interactions i ON s.id = i.session_id
    WHERE s.id = session_uuid
    GROUP BY s.id, s.start_time, s.end_time;
END;
$$ LANGUAGE plpgsql;

-- Function to generate daily statistics
CREATE OR REPLACE FUNCTION generate_daily_statistics(target_date DATE)
RETURNS void AS $$
BEGIN
    INSERT INTO daily_statistics (user_id, date, total_sessions, total_interactions, total_cost_usd, avg_session_duration_seconds, success_rate)
    SELECT 
        s.user_id,
        target_date,
        COUNT(DISTINCT s.id) as total_sessions,
        COUNT(i.id) as total_interactions,
        SUM(s.total_cost_usd) as total_cost_usd,
        AVG(EXTRACT(EPOCH FROM (COALESCE(s.end_time, NOW()) - s.start_time)))::INTEGER as avg_session_duration_seconds,
        AVG(CASE WHEN s.status = 'completed' THEN 1.0 ELSE 0.0 END) as success_rate
    FROM claude_sessions s
    LEFT JOIN claude_interactions i ON s.id = i.session_id
    WHERE DATE(s.start_time) = target_date
    GROUP BY s.user_id
    ON CONFLICT (user_id, date) 
    DO UPDATE SET
        total_sessions = EXCLUDED.total_sessions,
        total_interactions = EXCLUDED.total_interactions,
        total_cost_usd = EXCLUDED.total_cost_usd,
        avg_session_duration_seconds = EXCLUDED.avg_session_duration_seconds,
        success_rate = EXCLUDED.success_rate,
        created_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- Views for Common Queries
-- ========================================

-- Active sessions view
CREATE OR REPLACE VIEW active_sessions_view AS
SELECT 
    s.*,
    COUNT(i.id) as current_interaction_count,
    MAX(i.created_at) as last_interaction_at
FROM claude_sessions s
LEFT JOIN claude_interactions i ON s.id = i.session_id
WHERE s.status = 'active'
GROUP BY s.id;

-- User statistics summary view
CREATE OR REPLACE VIEW user_statistics_summary AS
SELECT 
    u.id as user_id,
    COUNT(DISTINCT s.id) as total_sessions,
    COUNT(DISTINCT CASE WHEN s.status = 'active' THEN s.id END) as active_sessions,
    SUM(s.total_interactions) as total_interactions,
    SUM(s.total_cost_usd) as total_cost,
    AVG(EXTRACT(EPOCH FROM (COALESCE(s.end_time, NOW()) - s.start_time))) as avg_session_duration_seconds
FROM auth.users u
LEFT JOIN claude_sessions s ON u.id = s.user_id
GROUP BY u.id;