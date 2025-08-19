#!/usr/bin/env python3
"""
Token estimation for built-in tools that don't report usage.
Rough estimates based on typical token/character ratios.
"""

import json
from typing import Dict, Any

def estimate_tokens(tool_name: str, tool_input: Dict[str, Any], tool_output: str = "") -> Dict[str, int]:
    """
    Estimate token usage for built-in tools.
    
    Character to token ratio approximations:
    - English text: ~4 characters per token
    - Code: ~3 characters per token  
    - JSON: ~2.5 characters per token
    """
    
    estimates = {
        "input_tokens": 0,
        "output_tokens": 0
    }
    
    if tool_name == "WebSearch":
        # Query tokens + tool invocation overhead
        query = tool_input.get("query", "")
        estimates["input_tokens"] = len(query) // 4 + 50  # 50 for tool schema
        
        # Response tokens (search results are typically 500-2000 tokens)
        if tool_output:
            estimates["output_tokens"] = len(tool_output) // 4
        else:
            estimates["output_tokens"] = 800  # Average search result
            
    elif tool_name == "WebFetch":
        # URL + prompt tokens
        url = tool_input.get("url", "")
        prompt = tool_input.get("prompt", "")
        estimates["input_tokens"] = (len(url) + len(prompt)) // 4 + 100
        
        # Fetched content (typically summarized to 1000-3000 tokens)
        if tool_output:
            estimates["output_tokens"] = min(len(tool_output) // 4, 3000)
        else:
            estimates["output_tokens"] = 1500
            
    elif tool_name in ["Read", "Glob", "Grep", "LS"]:
        # File operations
        estimates["input_tokens"] = 100  # Tool invocation
        if tool_output:
            # Code/file content uses more tokens
            estimates["output_tokens"] = len(tool_output) // 3
        else:
            estimates["output_tokens"] = 500
            
    elif tool_name == "Bash":
        # Command execution
        command = tool_input.get("command", "")
        estimates["input_tokens"] = len(command) // 3 + 50
        if tool_output:
            estimates["output_tokens"] = len(tool_output) // 3
        else:
            estimates["output_tokens"] = 200
            
    elif tool_name in ["Edit", "MultiEdit", "Write"]:
        # File modifications
        content = tool_input.get("new_string", "") or tool_input.get("content", "")
        old_content = tool_input.get("old_string", "")
        estimates["input_tokens"] = (len(content) + len(old_content)) // 3 + 100
        estimates["output_tokens"] = 50  # Confirmation message
        
    else:
        # Generic tool estimate
        input_str = json.dumps(tool_input) if isinstance(tool_input, dict) else str(tool_input)
        estimates["input_tokens"] = len(input_str) // 4 + 50
        if tool_output:
            estimates["output_tokens"] = len(tool_output) // 4
        else:
            estimates["output_tokens"] = 100
    
    return estimates