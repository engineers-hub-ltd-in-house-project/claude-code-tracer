-- Migration: 002_analytics_tables
-- Created: 2024-01-12
-- Description: Add analytics and reporting tables

BEGIN;

-- Daily aggregated statistics
CREATE TABLE daily_statistics (
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

-- Project analytics
CREATE TABLE project_analytics (
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

-- Privacy patterns
CREATE TABLE privacy_patterns (
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
CREATE TABLE audit_logs (
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

-- Export jobs
CREATE TABLE export_jobs (
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

-- Create indexes
CREATE INDEX idx_daily_stats_user_date ON daily_statistics(user_id, date DESC);
CREATE INDEX idx_project_analytics_user_project ON project_analytics(user_id, project_path);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Enable RLS
ALTER TABLE daily_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE privacy_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE export_jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own statistics" ON daily_statistics
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own project analytics" ON project_analytics
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own privacy patterns" ON privacy_patterns
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own audit logs" ON audit_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own export jobs" ON export_jobs
    FOR ALL USING (auth.uid() = user_id);

-- Update trigger for privacy patterns
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

COMMIT;