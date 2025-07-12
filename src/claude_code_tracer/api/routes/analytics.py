"""Analytics-related API endpoints."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Query

from claude_code_tracer.api.dependencies import (
    OptionalUser,
    SupabaseServiceDep,
)

router = APIRouter()


@router.get("/usage-stats")
async def get_usage_stats(
    supabase: SupabaseServiceDep,
    user: OptionalUser,
    period: str = Query("week", description="Period: day, week, month, year"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """Get usage statistics for the specified period."""
    # Default date range based on period
    if not end_date:
        end_date = datetime.utcnow()
    
    if not start_date:
        if period == "day":
            start_date = end_date - timedelta(days=1)
        elif period == "week":
            start_date = end_date - timedelta(weeks=1)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(weeks=1)
    
    user_id = user["id"] if user else None
    
    # Get sessions in date range
    sessions = await supabase.list_sessions(
        user_id=user_id,
        limit=1000,  # TODO: Implement date filtering in supabase service
    )
    
    # Filter by date range
    filtered_sessions = [
        s for s in sessions
        if start_date <= s.created_at <= end_date
    ]
    
    # Calculate stats
    total_sessions = len(filtered_sessions)
    total_interactions = sum(s.total_interactions for s in filtered_sessions)
    total_cost = sum(s.total_cost_usd for s in filtered_sessions)
    
    completed_sessions = [s for s in filtered_sessions if s.status == "completed"]
    success_rate = len(completed_sessions) / total_sessions if total_sessions > 0 else 0
    
    avg_duration = 0
    if completed_sessions:
        durations = [
            (s.end_time - s.start_time).total_seconds()
            for s in completed_sessions
            if s.end_time
        ]
        avg_duration = sum(durations) / len(durations) / 60 if durations else 0
    
    # Daily breakdown
    daily_stats = {}
    for session in filtered_sessions:
        date_key = session.created_at.date().isoformat()
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                "date": date_key,
                "sessions": 0,
                "interactions": 0,
                "cost_usd": 0,
            }
        daily_stats[date_key]["sessions"] += 1
        daily_stats[date_key]["interactions"] += session.total_interactions
        daily_stats[date_key]["cost_usd"] += session.total_cost_usd
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "stats": {
            "total_sessions": total_sessions,
            "total_interactions": total_interactions,
            "total_cost_usd": round(total_cost, 4),
            "avg_session_duration_minutes": round(avg_duration, 2),
            "success_rate": round(success_rate, 2),
        },
        "daily_breakdown": sorted(daily_stats.values(), key=lambda x: x["date"]),
    }


@router.post("/usage-patterns")
async def analyze_usage_patterns(
    supabase: SupabaseServiceDep,
    user: OptionalUser,
    days: int = Query(30, description="Number of days to analyze"),
    include_clustering: bool = Query(True, description="Include topic clustering"),
    include_recommendations: bool = Query(True, description="Include recommendations"),
):
    """Analyze usage patterns and provide insights."""
    user_id = user["id"] if user else None
    
    # Get recent sessions
    sessions = await supabase.list_sessions(
        user_id=user_id,
        limit=1000,
    )
    
    # Filter by date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    recent_sessions = [
        s for s in sessions
        if s.created_at >= cutoff_date
    ]
    
    # Analyze peak hours
    hour_counts = {}
    for session in recent_sessions:
        hour = session.created_at.hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    # Get top 4 peak hours
    peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:4]
    peak_hours = [hour for hour, _ in peak_hours]
    
    # Analyze common operations (would need interaction data)
    # For now, return placeholder data
    common_operations = [
        {"operation": "code_generation", "frequency": 0.35},
        {"operation": "debugging", "frequency": 0.28},
        {"operation": "refactoring", "frequency": 0.22},
        {"operation": "testing", "frequency": 0.15},
    ]
    
    # Topic clusters (placeholder - would need NLP analysis)
    topic_clusters = []
    if include_clustering:
        topic_clusters = [
            {
                "cluster_id": 0,
                "size": 45,
                "keywords": ["api", "endpoint", "fastapi"],
                "sample_prompts": ["Create a new API endpoint", "Add FastAPI route"],
            },
            {
                "cluster_id": 1,
                "size": 32,
                "keywords": ["test", "pytest", "coverage"],
                "sample_prompts": ["Write unit tests", "Improve test coverage"],
            },
        ]
    
    # Recommendations
    recommendations = []
    if include_recommendations:
        if peak_hours:
            recommendations.append(
                f"Your peak productivity hours are {', '.join(map(str, peak_hours[:2]))}:00. "
                "Consider scheduling complex tasks during these times."
            )
        
        if total_sessions := len(recent_sessions):
            avg_daily = total_sessions / days
            if avg_daily < 1:
                recommendations.append(
                    "You're using Claude Code less than once per day. "
                    "Consider integrating it more into your workflow."
                )
            elif avg_daily > 10:
                recommendations.append(
                    "You're a power user! Consider creating templates for common tasks."
                )
    
    return {
        "patterns": {
            "peak_hours": peak_hours,
            "common_operations": common_operations,
            "topic_clusters": topic_clusters,
        },
        "recommendations": recommendations,
        "analysis_period_days": days,
        "total_sessions_analyzed": len(recent_sessions),
    }