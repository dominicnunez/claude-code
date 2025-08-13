# Discord Claude Bridge Setup

## Features
- **Remote Claude prompting**: Send `!claude <prompt>` from Discord to run Claude commands
- **Interactive permissions**: Agents can request permission with Yes/No/Skip buttons
- **Status monitoring**: Check if Claude is running with `!status`
- **Notifications**: Get alerts when agents complete tasks

## Setup Instructions

### 1. Create Discord Bot
1. Go to https://discord.com/developers/applications
2. Click "New Application" and name it (e.g., "Claude Bridge")
3. Go to "Bot" section
4. Click "Reset Token" and copy the token
5. Enable "MESSAGE CONTENT INTENT" under Privileged Gateway Intents

### 2. Add Bot to Your Server
1. In Discord Developer Portal, go to "OAuth2" > "URL Generator"
2. Select scopes: `bot`, `applications.commands`
3. Select permissions: `Send Messages`, `Read Messages`, `Add Reactions`, `Embed Links`
4. Copy the generated URL and open it to add bot to your server

### 3. Get Channel ID and Server ID
1. In Discord, enable Developer Mode (Settings > Advanced > Developer Mode)
2. Right-click the channel you want to use > "Copy Channel ID"
3. Right-click your server name > "Copy Server ID"

### 4. Configure the Bridge
Create `~/.claude/discord_config.json`:
```json
{
  "token": "YOUR_BOT_TOKEN",
  "channel_id": "YOUR_CHANNEL_ID",
  "guild_id": "YOUR_SERVER_ID"
}
```

### 5. Install Dependencies
```bash
pip install discord.py
```

### 6. Run the Bridge
```bash
# For slash commands support:
python ~/.claude/discord_claude_slash.py

# Or for basic text commands:
python ~/.claude/discord_claude_bridge.py
```

## Usage Examples

### Discord Slash Commands (Mirrors Claude's):
- `/claude prompt: "what files are in src?"` - Send any prompt to Claude
- `/clear` - Clear conversation history
- `/status` - View Claude status
- `/cost` - Show token usage
- `/model model: claude-3-5-sonnet` - Change model
- `/review files: src/` - Request code review
- `/agents action: list` - Manage agents
- `/memory` - Edit CLAUDE.md files
- `/compact focus: "api implementation"` - Compact conversation
- `/init` - Initialize project with CLAUDE.md
- `/config` - View/modify configuration
- `/mcp action: list` - Manage MCP servers
- `/add_dir directory: /path/to/add` - Add working directory
- `/pr_comments pr_url: github.com/...` - View PR comments
- `/vim` - Enter vim mode
- `/help` - Get Claude help
- `/doctor` - Check installation health

### Text Commands (Legacy):
- `!claude what files are in the src folder?`
- `!status` - Check if Claude is running

### For Agents to Request Permission:
```python
import asyncio
from discord_claude_bridge import request_discord_permission

response = asyncio.run(request_discord_permission(
    agent_name="god",
    action="Delete 10 test files",
    context="Cleaning up /tmp/test_files/"
))

if response == "yes":
    # Proceed with action
    pass
elif response == "no":
    # Abort action
    pass
```

## Auto-start (Optional)
Add to your shell profile or use systemd service:
```bash
nohup python ~/.claude/discord_claude_bridge.py > ~/.claude/discord_bot.log 2>&1 &
```