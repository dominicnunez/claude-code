#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# ///

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import importlib.util

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Ensure log directory exists
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / 'post_tool_use.json'
        
        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Track token usage if token_tracker exists
        try:
            token_tracker = Path(__file__).parent / "token_tracker.py"
            if token_tracker.exists():
                # Prepare tracking event with all available data
                tracking_event = input_data.copy()
                tracking_event["event_type"] = "post_tool_use"
                tracking_event["timestamp"] = datetime.now().isoformat()
                
                # If no usage data provided, estimate for built-in tools
                if "usage" not in tracking_event and "tool_name" in tracking_event:
                    try:
                        # Load token estimator
                        estimator_path = Path(__file__).parent / "utils" / "estimate_tokens.py"
                        if estimator_path.exists():
                            spec = importlib.util.spec_from_file_location("estimate_tokens", estimator_path)
                            estimator = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(estimator)
                            
                            # Estimate tokens based on tool input/output
                            tool_name = tracking_event.get("tool_name", "")
                            tool_input = tracking_event.get("tool_input", {})
                            tool_output = tracking_event.get("tool_output", "")
                            
                            estimated_usage = estimator.estimate_tokens(tool_name, tool_input, tool_output)
                            tracking_event["usage"] = estimated_usage
                            tracking_event["usage_estimated"] = True
                    except Exception:
                        pass  # Fail silently on estimation errors
                
                subprocess.run(
                    ["uv", "run", str(token_tracker)],
                    input=json.dumps(tracking_event),
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env={**os.environ, "CLAUDE_CODE_HOOK_EVENT": "post_tool_use"}
                )
        except Exception:
            pass  # Fail silently
        
        # Pass through the event data unchanged
        print(json.dumps(input_data))
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Exit cleanly on any other error
        sys.exit(0)

if __name__ == '__main__':
    main()