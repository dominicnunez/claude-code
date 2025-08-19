#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "python-dateutil",
# ]
# ///
"""
Token usage tracking hook for Claude Code.
Tracks token usage across sessions and saves to a central file.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import fcntl
import time

TRACKING_FILE = Path.home() / ".claude" / "token_usage.json"
TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_tracking_data() -> Dict[str, Any]:
    """Load existing tracking data or create new structure."""
    if TRACKING_FILE.exists():
        try:
            with open(TRACKING_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    return {
        "total_usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_creation_tokens": 0,
            "total_tokens": 0
        },
        "sessions": [],
        "daily_usage": {},
        "model_usage": {},
        "last_updated": None
    }

def save_tracking_data(data: Dict[str, Any], max_retries: int = 3) -> bool:
    """Save tracking data with file locking to prevent conflicts."""
    for attempt in range(max_retries):
        try:
            with open(TRACKING_FILE, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                json.dump(data, f, indent=2, default=str)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return True
        except BlockingIOError:
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
            else:
                print(f"Warning: Could not acquire lock on {TRACKING_FILE}", file=sys.stderr)
                return False
        except Exception as e:
            print(f"Error saving tracking data: {e}", file=sys.stderr)
            return False
    return False

def extract_token_usage(event_data: Dict[str, Any]) -> Optional[Dict[str, int]]:
    """Extract token usage from various event types."""
    usage = {}
    
    # Check for direct usage data
    if "usage" in event_data:
        usage_data = event_data["usage"]
        if isinstance(usage_data, dict):
            usage["input_tokens"] = usage_data.get("input_tokens", 0)
            usage["output_tokens"] = usage_data.get("output_tokens", 0)
            usage["cache_read_tokens"] = usage_data.get("cache_read_tokens", 0)
            usage["cache_creation_tokens"] = usage_data.get("cache_creation_tokens", 0)
    
    # Check for metrics in telemetry data
    if "metrics" in event_data:
        metrics = event_data["metrics"]
        if isinstance(metrics, dict):
            usage["input_tokens"] = metrics.get("input_tokens", usage.get("input_tokens", 0))
            usage["output_tokens"] = metrics.get("output_tokens", usage.get("output_tokens", 0))
    
    # Check tool responses for token counts
    if "tool_response" in event_data:
        response = event_data["tool_response"]
        if isinstance(response, dict) and "token_count" in response:
            usage["output_tokens"] = response["token_count"]
    
    return usage if usage else None

def update_token_usage(event_type: str, event_data: Dict[str, Any]) -> None:
    """Update token usage based on event data."""
    
    # Extract token usage from event
    usage = extract_token_usage(event_data)
    if not usage:
        return
    
    # Load existing data
    tracking_data = load_tracking_data()
    
    # Get current date and session info
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.isoformat()
    
    # Extract model info
    model = event_data.get("model", "unknown")
    session_id = event_data.get("session_id", f"session_{int(time.time())}")
    
    # Calculate total tokens for this event
    total = sum(usage.values())
    
    # Update total usage
    for key, value in usage.items():
        tracking_data["total_usage"][key] = tracking_data["total_usage"].get(key, 0) + value
    tracking_data["total_usage"]["total_tokens"] = tracking_data["total_usage"].get("total_tokens", 0) + total
    
    # Update daily usage
    if date_str not in tracking_data["daily_usage"]:
        tracking_data["daily_usage"][date_str] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_creation_tokens": 0,
            "total_tokens": 0
        }
    
    for key, value in usage.items():
        tracking_data["daily_usage"][date_str][key] += value
    tracking_data["daily_usage"][date_str]["total_tokens"] += total
    
    # Update model usage
    if model not in tracking_data["model_usage"]:
        tracking_data["model_usage"][model] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_creation_tokens": 0,
            "total_tokens": 0,
            "request_count": 0
        }
    
    for key, value in usage.items():
        tracking_data["model_usage"][model][key] += value
    tracking_data["model_usage"][model]["total_tokens"] += total
    tracking_data["model_usage"][model]["request_count"] += 1
    
    # Add session entry
    session_entry = {
        "timestamp": timestamp,
        "session_id": session_id,
        "event_type": event_type,
        "model": model,
        "usage": usage,
        "total_tokens": total
    }
    
    # Keep only last 1000 session entries to prevent file from growing too large
    tracking_data["sessions"].append(session_entry)
    if len(tracking_data["sessions"]) > 1000:
        tracking_data["sessions"] = tracking_data["sessions"][-1000:]
    
    tracking_data["last_updated"] = timestamp
    
    # Save updated data
    save_tracking_data(tracking_data)

def main():
    """Main hook entry point."""
    # Read event data from stdin
    try:
        event_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    
    # Get event type
    event_type = os.environ.get("CLAUDE_CODE_HOOK_EVENT", "unknown")
    
    # Process token usage for relevant events
    relevant_events = [
        "post_tool_use",
        "stop",
        "notification",
        "subagent_stop",
        "session_end"
    ]
    
    if event_type in relevant_events or "usage" in event_data or "metrics" in event_data:
        try:
            update_token_usage(event_type, event_data)
        except Exception as e:
            print(f"Error updating token usage: {e}", file=sys.stderr)
    
    # Pass through the event data
    print(json.dumps(event_data))
    return 0

if __name__ == "__main__":
    sys.exit(main())