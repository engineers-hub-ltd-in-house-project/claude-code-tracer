-- Migration: 003_views_and_functions
-- Created: 2024-01-12
-- Description: Create views and helper functions

BEGIN;

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

-- Recent interactions view
CREATE OR REPLACE VIEW recent_interactions_view AS
SELECT 
    i.*,
    s.user_id,
    s.project_path,
    s.session_id as session_identifier
FROM claude_interactions i
JOIN claude_sessions s ON i.session_id = s.id
WHERE i.created_at > NOW() - INTERVAL '24 hours'
ORDER BY i.created_at DESC;

-- Function to get user's most used tools
CREATE OR REPLACE FUNCTION get_user_top_tools(
    p_user_id UUID,
    p_days INTEGER DEFAULT 30,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    tool_name TEXT,
    usage_count BIGINT,
    percentage DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH tool_usage AS (
        SELECT 
            jsonb_array_elements_text(i.tools_used) as tool_name,
            COUNT(*) as usage_count
        FROM claude_interactions i
        JOIN claude_sessions s ON i.session_id = s.id
        WHERE s.user_id = p_user_id
        AND s.start_time > NOW() - (p_days || ' days')::INTERVAL
        GROUP BY tool_name
    ),
    total_usage AS (
        SELECT SUM(usage_count) as total FROM tool_usage
    )
    SELECT 
        tu.tool_name,
        tu.usage_count,
        ROUND((tu.usage_count::DECIMAL / t.total * 100), 2) as percentage
    FROM tool_usage tu
    CROSS JOIN total_usage t
    ORDER BY tu.usage_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get project activity summary
CREATE OR REPLACE FUNCTION get_project_activity_summary(
    p_user_id UUID,
    p_project_path TEXT,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    total_sessions BIGINT,
    total_interactions BIGINT,
    total_cost DECIMAL(10,6),
    avg_session_length_minutes INTEGER,
    success_rate DECIMAL(5,2),
    most_active_hour INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT s.id) as total_sessions,
        COUNT(i.id) as total_interactions,
        SUM(s.total_cost_usd) as total_cost,
        (AVG(EXTRACT(EPOCH FROM (COALESCE(s.end_time, NOW()) - s.start_time))) / 60)::INTEGER as avg_session_length_minutes,
        ROUND(AVG(CASE WHEN s.status = 'completed' THEN 100.0 ELSE 0.0 END), 2) as success_rate,
        MODE() WITHIN GROUP (ORDER BY EXTRACT(HOUR FROM s.start_time))::INTEGER as most_active_hour
    FROM claude_sessions s
    LEFT JOIN claude_interactions i ON s.id = i.session_id
    WHERE s.user_id = p_user_id
    AND s.project_path = p_project_path
    AND s.start_time > NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- Function to search interactions
CREATE OR REPLACE FUNCTION search_interactions(
    p_user_id UUID,
    p_search_term TEXT,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    interaction_id UUID,
    session_id UUID,
    message_type VARCHAR(50),
    content TEXT,
    created_at TIMESTAMPTZ,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id as interaction_id,
        i.session_id,
        i.message_type,
        COALESCE(i.user_prompt, i.claude_response) as content,
        i.created_at,
        ts_rank(
            to_tsvector('english', COALESCE(i.user_prompt, '') || ' ' || COALESCE(i.claude_response, '')),
            plainto_tsquery('english', p_search_term)
        ) as relevance
    FROM claude_interactions i
    JOIN claude_sessions s ON i.session_id = s.id
    WHERE s.user_id = p_user_id
    AND (
        to_tsvector('english', COALESCE(i.user_prompt, '') || ' ' || COALESCE(i.claude_response, ''))
        @@ plainto_tsquery('english', p_search_term)
    )
    ORDER BY relevance DESC, i.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get cost breakdown by model
CREATE OR REPLACE FUNCTION get_cost_breakdown_by_model(
    p_user_id UUID,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    model_name TEXT,
    session_count BIGINT,
    total_cost DECIMAL(10,6),
    avg_cost_per_session DECIMAL(10,6)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(metadata->>'model', 'unknown') as model_name,
        COUNT(*) as session_count,
        SUM(total_cost_usd) as total_cost,
        AVG(total_cost_usd) as avg_cost_per_session
    FROM claude_sessions
    WHERE user_id = p_user_id
    AND DATE(start_time) BETWEEN p_start_date AND p_end_date
    GROUP BY model_name
    ORDER BY total_cost DESC;
END;
$$ LANGUAGE plpgsql;

-- Create text search indexes
CREATE INDEX idx_interactions_user_prompt_gin ON claude_interactions 
    USING gin(to_tsvector('english', user_prompt));

CREATE INDEX idx_interactions_claude_response_gin ON claude_interactions 
    USING gin(to_tsvector('english', claude_response));

COMMIT;