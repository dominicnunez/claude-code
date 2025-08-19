#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import argparse
import json
import os
import sys
import random
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def get_completion_messages():
    """Return list of friendly completion messages."""
    return [
        "Work complete!",
        "All done!",
        "Task finished!",
        "Job complete!",
        "Ready for next task!"
    ]


def get_tts_script_path():
    """
    Determine which TTS script to use based on available API keys.
    Priority order: ElevenLabs > OpenAI > pyttsx3
    """
    # Get current script directory and construct utils/tts path
    script_dir = Path(__file__).parent
    tts_dir = script_dir / "utils" / "tts"
    
    # Check for ElevenLabs API key (highest priority)
    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_script = tts_dir / "elevenlabs_tts.py"
        if elevenlabs_script.exists():
            return str(elevenlabs_script)
    
    # Check for OpenAI API key (second priority)
    if os.getenv('OPENAI_API_KEY'):
        openai_script = tts_dir / "openai_tts.py"
        if openai_script.exists():
            return str(openai_script)
    
    # Fall back to pyttsx3 (no API key required)
    pyttsx3_script = tts_dir / "pyttsx3_tts.py"
    if pyttsx3_script.exists():
        return str(pyttsx3_script)
    
    return None


def get_llm_completion_message():
    """
    Generate completion message using available LLM services.
    Priority order: OpenAI > Anthropic > fallback to random message
    
    Returns:
        str: Generated or fallback completion message
    """
    # Get current script directory and construct utils/llm path
    script_dir = Path(__file__).parent
    llm_dir = script_dir / "utils" / "llm"
    
    # Try OpenAI first (highest priority)
    if os.getenv('OPENAI_API_KEY'):
        oai_script = llm_dir / "oai.py"
        if oai_script.exists():
            try:
                result = subprocess.run([
                    "uv", "run", str(oai_script), "--completion"
                ], 
                capture_output=True,
                text=True,
                timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
    
    # Try Anthropic second
    if os.getenv('ANTHROPIC_API_KEY'):
        anth_script = llm_dir / "anth.py"
        if anth_script.exists():
            try:
                result = subprocess.run([
                    "uv", "run", str(anth_script), "--completion"
                ], 
                capture_output=True,
                text=True,
                timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
    
    # Fallback to random predefined message
    messages = get_completion_messages()
    return random.choice(messages)

def get_session_token_usage(session_id: str) -> Optional[Dict[str, Any]]:
    """Get token usage statistics for a specific session."""
    try:
        token_file = Path.home() / ".claude" / "token_usage.json"
        if not token_file.exists():
            return None
        
        with open(token_file, 'r') as f:
            data = json.load(f)
        
        # Find all events for this session
        session_events = [s for s in data.get("sessions", []) 
                         if s.get("session_id") == session_id]
        
        if not session_events:
            return None
        
        # Aggregate token usage
        total_input = 0
        total_output = 0
        total_cache_read = 0
        total_cache_creation = 0
        models_used = set()
        
        for event in session_events:
            usage = event.get("usage", {})
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)
            total_cache_read += usage.get("cache_read_tokens", 0)
            total_cache_creation += usage.get("cache_creation_tokens", 0)
            
            model = event.get("model")
            if model and model != "unknown":
                models_used.add(model)
        
        total_tokens = total_input + total_output + total_cache_read + total_cache_creation
        
        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "cache_read_tokens": total_cache_read,
            "cache_creation_tokens": total_cache_creation,
            "total_tokens": total_tokens,
            "models": list(models_used)
        }
    except Exception:
        return None

def calculate_session_cost(usage: Dict[str, Any], models: list) -> float:
    """Calculate estimated cost for session usage."""
    # Use the most expensive model for conservative estimate
    model_pricing = {
        "opus": {"input": 15.00, "output": 75.00, "cache_read": 1.50, "cache_creation": 18.75},
        "sonnet": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_creation": 3.75},
        "haiku": {"input": 0.80, "output": 4.00, "cache_read": 0.08, "cache_creation": 1.00},
    }
    
    # Determine pricing tier based on models used
    pricing = model_pricing["sonnet"]  # Default
    for model in models:
        model_lower = model.lower() if model else ""
        if "opus" in model_lower:
            pricing = model_pricing["opus"]
            break  # Opus is most expensive, use it
        elif "haiku" in model_lower and pricing == model_pricing["sonnet"]:
            pricing = model_pricing["haiku"]
    
    cost = 0
    cost += (usage.get("input_tokens", 0) / 1_000_000) * pricing["input"]
    cost += (usage.get("output_tokens", 0) / 1_000_000) * pricing["output"]
    cost += (usage.get("cache_read_tokens", 0) / 1_000_000) * pricing["cache_read"]
    cost += (usage.get("cache_creation_tokens", 0) / 1_000_000) * pricing["cache_creation"]
    
    return cost

def display_session_summary(session_id: str) -> str:
    """Generate a session summary with token usage and cost."""
    usage = get_session_token_usage(session_id)
    
    if not usage or usage["total_tokens"] == 0:
        return ""
    
    cost = calculate_session_cost(usage, usage.get("models", []))
    
    # Format the summary
    summary_lines = [
        "\n" + "="*50,
        "SESSION TOKEN USAGE SUMMARY",
        "="*50,
        f"Input tokens:    {usage['input_tokens']:,}",
        f"Output tokens:   {usage['output_tokens']:,}",
        f"Cache tokens:    {usage['cache_read_tokens'] + usage['cache_creation_tokens']:,}",
        "-"*50,
        f"Total tokens:    {usage['total_tokens']:,}",
        f"Estimated cost:  ${cost:.4f}",
    ]
    
    if usage.get("models"):
        summary_lines.append(f"Models used:     {', '.join(usage['models'][:2])}")
    
    summary_lines.append("="*50)
    
    return "\n".join(summary_lines)

def announce_completion():
    """Announce completion using the best available TTS service."""
    try:
        tts_script = get_tts_script_path()
        if not tts_script:
            return  # No TTS scripts available
        
        # Get completion message (LLM-generated or fallback)
        completion_message = get_llm_completion_message()
        
        # Call the TTS script with the completion message
        subprocess.run([
            "uv", "run", tts_script, completion_message
        ], 
        capture_output=True,  # Suppress output
        timeout=10  # 10-second timeout
        )
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # Fail silently if TTS encounters issues
        pass
    except Exception:
        # Fail silently for any other errors
        pass


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--chat', action='store_true', help='Copy transcript to chat.json')
        args = parser.parse_args()
        
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract required fields
        session_id = input_data.get("session_id", "")
        stop_hook_active = input_data.get("stop_hook_active", False)

        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "stop.json")

        # Read existing log data or initialize empty list
        if os.path.exists(log_path):
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
        
        # Track token usage for this session
        try:
            token_tracker = Path(__file__).parent / "token_tracker.py"
            if token_tracker.exists():
                subprocess.run(
                    ["uv", "run", str(token_tracker)],
                    input=json.dumps(input_data),
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env={**os.environ, "CLAUDE_CODE_HOOK_EVENT": "stop"}
                )
        except Exception:
            pass  # Fail silently
        
        # Handle --chat switch
        if args.chat and 'transcript_path' in input_data:
            transcript_path = input_data['transcript_path']
            if os.path.exists(transcript_path):
                # Read .jsonl file and convert to JSON array
                chat_data = []
                try:
                    with open(transcript_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    chat_data.append(json.loads(line))
                                except json.JSONDecodeError:
                                    pass  # Skip invalid lines
                    
                    # Write to logs/chat.json
                    chat_file = os.path.join(log_dir, 'chat.json')
                    with open(chat_file, 'w') as f:
                        json.dump(chat_data, f, indent=2)
                except Exception:
                    pass  # Fail silently

        # Display session token usage summary (unless disabled)
        show_summary = os.environ.get('CLAUDE_SHOW_TOKEN_SUMMARY', 'true').lower() != 'false'
        if show_summary:
            try:
                summary = display_session_summary(session_id)
                if summary:
                    print(summary, file=sys.stderr)  # Print to stderr so it's visible
            except Exception:
                pass  # Fail silently if display fails
        
        # Announce completion via TTS
        announce_completion()

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()
