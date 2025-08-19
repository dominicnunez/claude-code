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
import subprocess
import re
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


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


def extract_token_usage(output_text):
    """Extract token usage from subagent output text."""
    usage = {}
    
    # Common patterns for token reporting
    patterns = [
        # Pattern: "57k tokens" or "57,000 tokens"
        r'([\d,]+)k?\s*tokens?',
        # Pattern: "input_tokens: 30000, output_tokens: 27000"
        r'input_tokens[:\s]+([\d,]+)',
        r'output_tokens[:\s]+([\d,]+)',
        # Pattern: "Total tokens: 57000" or "Total: 57,000 tokens"
        r'[Tt]otal(?:\s+tokens)?[:\s]+([\d,]+)',
        # Pattern: "Used 57000 tokens"
        r'[Uu]sed\s+([\d,]+)\s*tokens?',
    ]
    
    # Try to find total tokens first - look for various patterns
    patterns = [
        r'[Tt]otal.*?[:\s]+?([\d,]+)(k)?\s*tokens?',  # "Total token usage: 42,500"
        r'[Tt]oken\s+(?:count|usage)[:\s]+?([\d,]+)(k)?',  # "Token count: 15000"
        r'[Uu]sed\s+([\d,]+)(k)?\s*tokens?',  # "Used 57k tokens"
        r'consumed\s+([\d,]+)(k)?\s*tokens?',  # "consumed 8k tokens"
        r'([\d,]+)(k)?\s*tokens?',  # Generic "57k tokens"
    ]
    
    total_match = None
    for pattern in patterns:
        total_match = re.search(pattern, output_text, re.IGNORECASE)
        if total_match:
            break
    
    if total_match:
        total_str = total_match.group(1).replace(',', '')
        if total_match.group(2) and total_match.group(2).lower() == 'k':
            total_tokens = int(float(total_str) * 1000)
        else:
            total_tokens = int(total_str)
        
        # If we only have total, split it roughly 55/45 for input/output
        usage['input_tokens'] = int(total_tokens * 0.55)
        usage['output_tokens'] = total_tokens - usage['input_tokens']
        usage['total_tokens'] = total_tokens
    
    # Try to find specific input/output tokens
    input_match = re.search(r'input_tokens[:\s]+([\d,]+)', output_text, re.IGNORECASE)
    output_match = re.search(r'output_tokens[:\s]+([\d,]+)', output_text, re.IGNORECASE)
    
    if input_match:
        usage['input_tokens'] = int(input_match.group(1).replace(',', ''))
    if output_match:
        usage['output_tokens'] = int(output_match.group(1).replace(',', ''))
    
    # Calculate total if we have input and output
    if 'input_tokens' in usage and 'output_tokens' in usage and 'total_tokens' not in usage:
        usage['total_tokens'] = usage['input_tokens'] + usage['output_tokens']
    
    # Add default cache values
    if usage:
        usage['cache_read_tokens'] = 0
        usage['cache_creation_tokens'] = 0
    
    return usage if usage else None


def track_subagent_tokens(input_data):
    """Track token usage from subagent execution."""
    try:
        # Look for token usage in various places
        usage = None
        
        # Check if usage is directly provided
        if 'usage' in input_data:
            usage = input_data['usage']
        
        # Try to extract from agent output if available
        if not usage and 'agent_output' in input_data:
            usage = extract_token_usage(input_data['agent_output'])
        
        # Try to extract from result if available
        if not usage and 'result' in input_data:
            result_text = str(input_data.get('result', ''))
            usage = extract_token_usage(result_text)
        
        # Try to extract from any text field
        if not usage:
            for key in ['output', 'response', 'message', 'content']:
                if key in input_data:
                    text = str(input_data.get(key, ''))
                    usage = extract_token_usage(text)
                    if usage:
                        break
        
        if usage:
            # Call token_tracker.py with the usage data
            token_tracker = Path(__file__).parent / "token_tracker.py"
            if token_tracker.exists():
                tracking_event = {
                    "session_id": input_data.get("session_id", "subagent"),
                    "event_type": "subagent_stop",
                    "usage": usage,
                    "model": input_data.get("model", input_data.get("agent_type", "unknown")),
                    "timestamp": datetime.now().isoformat(),
                    "agent_type": input_data.get("agent_type", "unknown")
                }
                
                subprocess.run(
                    ["python3", str(token_tracker)],
                    input=json.dumps(tracking_event),
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env={**os.environ, "CLAUDE_CODE_HOOK_EVENT": "subagent_stop"}
                )
                
                # Log that we tracked tokens
                print(f"Tracked {usage.get('total_tokens', 0)} tokens for subagent", file=sys.stderr)
    except Exception as e:
        # Fail silently but log to stderr for debugging
        print(f"Token tracking error: {e}", file=sys.stderr)


def announce_subagent_completion():
    """Announce subagent completion using the best available TTS service."""
    try:
        tts_script = get_tts_script_path()
        if not tts_script:
            return  # No TTS scripts available
        
        # Use fixed message for subagent completion
        completion_message = "Subagent Complete"
        
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
        log_path = os.path.join(log_dir, "subagent_stop.json")

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
        
        # Handle --chat switch (same as stop.py)
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

        # Track token usage if available
        track_subagent_tokens(input_data)
        
        # Announce subagent completion via TTS
        announce_subagent_completion()

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()