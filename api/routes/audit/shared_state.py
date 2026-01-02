"""
Shared state for audit routes.
In-memory cache for report HTML content and progress tracking.
In production, use Redis or database.
"""
# In-memory store for report HTML content (for async jobs)
_report_cache = {}

# Track running background tasks for cancellation
_running_tasks = {}


def get_report_cache():
    """Get the report cache dictionary."""
    return _report_cache


def get_running_tasks():
    """Get the running tasks dictionary."""
    return _running_tasks

