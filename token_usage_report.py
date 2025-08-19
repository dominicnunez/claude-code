#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
#     "python-dateutil",
# ]
# ///
"""
Token usage reporting tool for Claude Code.
Displays comprehensive token usage statistics from tracked data.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from dateutil import parser as date_parser

console = Console()
TRACKING_FILE = Path.home() / ".claude" / "token_usage.json"

def load_tracking_data() -> Optional[Dict[str, Any]]:
    """Load tracking data from file."""
    if not TRACKING_FILE.exists():
        return None
    
    try:
        with open(TRACKING_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        console.print(f"[red]Error loading tracking data: {e}[/red]")
        return None

def format_number(num: int) -> str:
    """Format large numbers with commas."""
    return f"{num:,}"

def calculate_cost(tokens: Dict[str, int], model: str = "claude-3-5-sonnet", context_length: int = 0) -> float:
    """
    Calculate estimated cost based on token usage.
    Prices from official Anthropic API pricing (August 2025).
    """
    # Official Anthropic pricing per 1M tokens (as of August 2025)
    pricing = {
        # Claude Opus 4.1 (Latest flagship model)
        "claude-opus-4-1": {
            "input": 15.00,
            "output": 75.00,
            "cache_read": 1.50,
            "cache_creation": 18.75,
        },
        "claude-opus-4-1-20250805": {  # Specific version
            "input": 15.00,
            "output": 75.00,
            "cache_read": 1.50,
            "cache_creation": 18.75,
        },
        # Claude Sonnet 4 (context-dependent pricing)
        "claude-sonnet-4": {
            "input": 3.00 if context_length <= 200000 else 6.00,
            "output": 15.00 if context_length <= 200000 else 22.50,
            "cache_read": 0.30 if context_length <= 200000 else 0.60,
            "cache_creation": 3.75 if context_length <= 200000 else 7.50,
        },
        # Claude 3.5 Sonnet (legacy pricing)
        "claude-3-5-sonnet": {
            "input": 3.00,
            "output": 15.00,
            "cache_read": 0.30,
            "cache_creation": 3.75,
        },
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,
            "output": 15.00,
            "cache_read": 0.30,
            "cache_creation": 3.75,
        },
        # Claude 3.5 Haiku (fast and efficient)
        "claude-3-5-haiku": {
            "input": 0.80,
            "output": 4.00,
            "cache_read": 0.08,
            "cache_creation": 1.00,
        },
        "claude-3-5-haiku-20241022": {
            "input": 0.80,
            "output": 4.00,
            "cache_read": 0.08,
            "cache_creation": 1.00,
        },
        # Claude 3 Opus (legacy)
        "claude-3-opus": {
            "input": 15.00,
            "output": 75.00,
            "cache_read": 1.50,
            "cache_creation": 18.75,
        },
        "claude-3-opus-20240229": {
            "input": 15.00,
            "output": 75.00,
            "cache_read": 1.50,
            "cache_creation": 18.75,
        },
    }
    
    # Determine model pricing based on model name
    model_lower = model.lower() if model else "unknown"
    
    # Try exact match first
    if model in pricing:
        model_pricing = pricing[model]
    # Check for model family matches
    elif "opus-4-1" in model_lower or "opus 4.1" in model_lower:
        model_pricing = pricing["claude-opus-4-1"]
    elif "sonnet-4" in model_lower or "sonnet 4" in model_lower:
        model_pricing = pricing["claude-sonnet-4"]
    elif "haiku" in model_lower:
        model_pricing = pricing["claude-3-5-haiku"]
    elif "opus" in model_lower:
        model_pricing = pricing["claude-3-opus"]
    elif "sonnet" in model_lower:
        model_pricing = pricing["claude-3-5-sonnet"]
    else:
        # Default to Sonnet 3.5 pricing for unknown models
        model_pricing = pricing["claude-3-5-sonnet"]
    
    cost = 0
    cost += (tokens.get("input_tokens", 0) / 1_000_000) * model_pricing["input"]
    cost += (tokens.get("output_tokens", 0) / 1_000_000) * model_pricing["output"]
    cost += (tokens.get("cache_read_tokens", 0) / 1_000_000) * model_pricing["cache_read"]
    cost += (tokens.get("cache_creation_tokens", 0) / 1_000_000) * model_pricing["cache_creation"]
    
    return cost

def display_total_usage(data: Dict[str, Any]) -> None:
    """Display total usage statistics."""
    total = data.get("total_usage", {})
    
    # Create main stats table
    table = Table(title="Total Token Usage", show_header=True, header_style="bold magenta")
    table.add_column("Token Type", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="green")
    
    table.add_row("Input Tokens", format_number(total.get("input_tokens", 0)))
    table.add_row("Output Tokens", format_number(total.get("output_tokens", 0)))
    table.add_row("Cache Read Tokens", format_number(total.get("cache_read_tokens", 0)))
    table.add_row("Cache Creation Tokens", format_number(total.get("cache_creation_tokens", 0)))
    table.add_row("", "")  # Empty row for separation
    table.add_row("[bold]Total Tokens[/bold]", f"[bold]{format_number(total.get('total_tokens', 0))}[/bold]")
    
    # Calculate estimated cost with detailed breakdown
    est_cost = calculate_cost(total)
    table.add_row("[yellow]Estimated Cost[/yellow]", f"[yellow]${est_cost:.4f}[/yellow]")
    
    # Add cost breakdown
    if est_cost > 0.01:  # Only show breakdown if cost is significant
        input_cost = (total.get("input_tokens", 0) / 1_000_000) * 3.00  # Default Sonnet pricing
        output_cost = (total.get("output_tokens", 0) / 1_000_000) * 15.00
        cache_cost = ((total.get("cache_read_tokens", 0) / 1_000_000) * 0.30 + 
                     (total.get("cache_creation_tokens", 0) / 1_000_000) * 3.75)
        
        table.add_row("", "")
        table.add_row("[dim]Input Cost[/dim]", f"[dim]${input_cost:.4f}[/dim]")
        table.add_row("[dim]Output Cost[/dim]", f"[dim]${output_cost:.4f}[/dim]")
        table.add_row("[dim]Cache Cost[/dim]", f"[dim]${cache_cost:.4f}[/dim]")
    
    console.print(table)

def display_daily_usage(data: Dict[str, Any], days: int = 7) -> None:
    """Display daily usage for the last N days."""
    daily = data.get("daily_usage", {})
    if not daily:
        console.print("[yellow]No daily usage data available.[/yellow]")
        return
    
    # Sort dates and get last N days
    sorted_dates = sorted(daily.keys(), reverse=True)[:days]
    
    table = Table(title=f"Daily Usage (Last {days} Days)", show_header=True, header_style="bold magenta")
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Input", justify="right", style="green")
    table.add_column("Output", justify="right", style="green")
    table.add_column("Cache", justify="right", style="blue")
    table.add_column("Total", justify="right", style="yellow")
    table.add_column("Est. Cost", justify="right", style="red")
    
    for date_str in sorted_dates:
        usage = daily[date_str]
        cache_total = usage.get("cache_read_tokens", 0) + usage.get("cache_creation_tokens", 0)
        cost = calculate_cost(usage)
        
        table.add_row(
            date_str,
            format_number(usage.get("input_tokens", 0)),
            format_number(usage.get("output_tokens", 0)),
            format_number(cache_total),
            format_number(usage.get("total_tokens", 0)),
            f"${cost:.4f}"
        )
    
    console.print(table)

def display_model_usage(data: Dict[str, Any]) -> None:
    """Display usage by model."""
    models = data.get("model_usage", {})
    if not models:
        console.print("[yellow]No model usage data available.[/yellow]")
        return
    
    table = Table(title="Usage by Model", show_header=True, header_style="bold magenta")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Requests", justify="right", style="blue")
    table.add_column("Total Tokens", justify="right", style="green")
    table.add_column("Avg/Request", justify="right", style="yellow")
    table.add_column("Est. Cost", justify="right", style="red")
    
    for model, usage in models.items():
        requests = usage.get("request_count", 0)
        total = usage.get("total_tokens", 0)
        avg = total // requests if requests > 0 else 0
        
        # Pass full model name for accurate pricing
        cost = calculate_cost(usage, model)
        
        # Format model name for display
        display_model = model
        if len(display_model) > 40:
            display_model = display_model[:37] + "..."
        
        table.add_row(
            display_model,
            format_number(requests),
            format_number(total),
            format_number(avg),
            f"${cost:.4f}"
        )
    
    console.print(table)

def display_recent_sessions(data: Dict[str, Any], count: int = 10) -> None:
    """Display recent session activity."""
    sessions = data.get("sessions", [])
    if not sessions:
        console.print("[yellow]No session data available.[/yellow]")
        return
    
    # Get last N sessions
    recent = sessions[-count:] if len(sessions) > count else sessions
    recent.reverse()  # Show most recent first
    
    table = Table(title=f"Recent Sessions (Last {count})", show_header=True, header_style="bold magenta")
    table.add_column("Time", style="cyan", no_wrap=True)
    table.add_column("Event", style="blue")
    table.add_column("Model", style="green")
    table.add_column("Tokens", justify="right", style="yellow")
    
    for session in recent:
        timestamp = session.get("timestamp", "")
        try:
            dt = date_parser.parse(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = timestamp[:16] if timestamp else "Unknown"
        
        event = session.get("event_type", "unknown")
        model = session.get("model", "unknown")
        if len(model) > 20:
            model = model[:17] + "..."
        
        total = session.get("total_tokens", 0)
        
        table.add_row(time_str, event, model, format_number(total))
    
    console.print(table)

def export_to_csv(data: Dict[str, Any], output_file: str) -> None:
    """Export usage data to CSV format."""
    import csv
    
    sessions = data.get("sessions", [])
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp", "Session ID", "Event Type", "Model",
            "Input Tokens", "Output Tokens", "Cache Read", "Cache Creation", "Total"
        ])
        
        for session in sessions:
            usage = session.get("usage", {})
            writer.writerow([
                session.get("timestamp", ""),
                session.get("session_id", ""),
                session.get("event_type", ""),
                session.get("model", ""),
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
                usage.get("cache_read_tokens", 0),
                usage.get("cache_creation_tokens", 0),
                session.get("total_tokens", 0)
            ])
    
    console.print(f"[green]Data exported to {output_file}[/green]")

def main():
    parser = argparse.ArgumentParser(description="View Claude Code token usage statistics")
    parser.add_argument("--daily", type=int, metavar="DAYS", help="Show daily usage for last N days")
    parser.add_argument("--sessions", type=int, metavar="COUNT", help="Show last N sessions")
    parser.add_argument("--models", action="store_true", help="Show usage by model")
    parser.add_argument("--export", metavar="FILE", help="Export data to CSV file")
    parser.add_argument("--raw", action="store_true", help="Show raw JSON data")
    
    args = parser.parse_args()
    
    # Load tracking data
    data = load_tracking_data()
    if not data:
        console.print("[red]No tracking data found.[/red]")
        console.print(f"[yellow]Expected file: {TRACKING_FILE}[/yellow]")
        console.print("\n[cyan]Token tracking will begin automatically when you start using Claude Code.[/cyan]")
        return
    
    # Handle raw output
    if args.raw:
        console.print_json(json.dumps(data, indent=2, default=str))
        return
    
    # Handle export
    if args.export:
        export_to_csv(data, args.export)
        return
    
    # Display header
    last_updated = data.get("last_updated", "Unknown")
    console.print(Panel.fit(
        f"[bold cyan]Claude Code Token Usage Report[/bold cyan]\n"
        f"Last Updated: {last_updated}",
        border_style="blue"
    ))
    console.print()
    
    # Display requested information or default view
    if args.daily:
        display_daily_usage(data, args.daily)
    elif args.sessions:
        display_recent_sessions(data, args.sessions)
    elif args.models:
        display_model_usage(data)
    else:
        # Default view: show everything
        display_total_usage(data)
        console.print()
        display_daily_usage(data, 7)
        console.print()
        display_model_usage(data)
        console.print()
        display_recent_sessions(data, 5)

if __name__ == "__main__":
    main()