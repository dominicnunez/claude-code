#!/usr/bin/env python3

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import subprocess
import json
import os
from datetime import datetime
from typing import Optional

class ClaudeDiscordBridge:
    def __init__(self, token, channel_id, guild_id):
        self.token = token
        self.channel_id = int(channel_id)
        self.guild_id = int(guild_id)
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=self.intents)
        
        self.setup_handlers()
        self.setup_slash_commands()
    
    def setup_handlers(self):
        @self.bot.event
        async def on_ready():
            print(f'Discord bot connected as {self.bot.user}')
            self.channel = self.bot.get_channel(self.channel_id)
            
            # Sync slash commands
            try:
                guild = discord.Object(id=self.guild_id)
                synced = await self.bot.tree.sync(guild=guild)
                print(f'Synced {len(synced)} slash commands')
            except Exception as e:
                print(f'Failed to sync commands: {e}')
    
    def setup_slash_commands(self):
        guild = discord.Object(id=self.guild_id)
        
        # Main Claude prompt command
        @self.bot.tree.command(name='claude', description='Send a prompt to Claude', guild=guild)
        @app_commands.describe(prompt='Your prompt for Claude')
        async def claude_prompt(interaction: discord.Interaction, prompt: str):
            await interaction.response.defer()
            
            try:
                result = subprocess.run(
                    ['claude', prompt],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=os.path.expanduser('~')
                )
                
                response = result.stdout or result.stderr
                
                # Split long responses
                if len(response) > 1900:
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    await interaction.followup.send(f"```\n{chunks[0]}\n```")
                    for chunk in chunks[1:]:
                        await interaction.channel.send(f"```\n{chunk}\n```")
                else:
                    await interaction.followup.send(f"```\n{response}\n```")
                    
            except subprocess.TimeoutExpired:
                await interaction.followup.send("⏱️ Command timed out")
            except Exception as e:
                await interaction.followup.send(f"❌ Error: {str(e)}")
        
        # Claude slash commands mapping
        @self.bot.tree.command(name='clear', description='Clear Claude conversation history', guild=guild)
        async def clear_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/clear')
        
        @self.bot.tree.command(name='init', description='Initialize project with CLAUDE.md guide', guild=guild)
        async def init_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/init')
        
        @self.bot.tree.command(name='status', description='View Claude account and system status', guild=guild)
        async def status_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/status')
        
        @self.bot.tree.command(name='cost', description='Show Claude token usage statistics', guild=guild)
        async def cost_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/cost')
        
        @self.bot.tree.command(name='model', description='Select or change Claude AI model', guild=guild)
        @app_commands.describe(model='Model to switch to (e.g., claude-3-5-sonnet-20241022)')
        async def model_cmd(interaction: discord.Interaction, model: Optional[str] = None):
            cmd = f'/model {model}' if model else '/model'
            await self.run_claude_slash_command(interaction, cmd)
        
        @self.bot.tree.command(name='review', description='Request code review from Claude', guild=guild)
        @app_commands.describe(files='Files or directories to review')
        async def review_cmd(interaction: discord.Interaction, files: Optional[str] = None):
            cmd = f'/review {files}' if files else '/review'
            await self.run_claude_slash_command(interaction, cmd)
        
        @self.bot.tree.command(name='compact', description='Compact conversation with optional focus', guild=guild)
        @app_commands.describe(focus='Optional focus area for compaction')
        async def compact_cmd(interaction: discord.Interaction, focus: Optional[str] = None):
            cmd = f'/compact {focus}' if focus else '/compact'
            await self.run_claude_slash_command(interaction, cmd)
        
        @self.bot.tree.command(name='agents', description='List or create Claude AI subagents', guild=guild)
        @app_commands.describe(action='list, create, or agent name')
        async def agents_cmd(interaction: discord.Interaction, action: Optional[str] = None):
            cmd = f'/agents {action}' if action else '/agents'
            await self.run_claude_slash_command(interaction, cmd)
        
        @self.bot.tree.command(name='memory', description='Edit CLAUDE.md memory files', guild=guild)
        @app_commands.describe(action='open, edit, or view')
        async def memory_cmd(interaction: discord.Interaction, action: Optional[str] = None):
            cmd = f'/memory {action}' if action else '/memory'
            await self.run_claude_slash_command(interaction, cmd)
        
        @self.bot.tree.command(name='permissions', description='View or update Claude permissions', guild=guild)
        async def permissions_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/permissions')
        
        @self.bot.tree.command(name='config', description='View or modify Claude configuration', guild=guild)
        @app_commands.describe(setting='Configuration setting to view/modify')
        async def config_cmd(interaction: discord.Interaction, setting: Optional[str] = None):
            cmd = f'/config {setting}' if setting else '/config'
            await self.run_claude_slash_command(interaction, cmd)
        
        @self.bot.tree.command(name='mcp', description='Manage MCP server connections', guild=guild)
        @app_commands.describe(action='list, connect, or disconnect')
        async def mcp_cmd(interaction: discord.Interaction, action: Optional[str] = None):
            cmd = f'/mcp {action}' if action else '/mcp'
            await self.run_claude_slash_command(interaction, cmd)
        
        @self.bot.tree.command(name='add_dir', description='Add additional working directories', guild=guild)
        @app_commands.describe(directory='Directory path to add')
        async def add_dir_cmd(interaction: discord.Interaction, directory: str):
            await self.run_claude_slash_command(interaction, f'/add-dir {directory}')
        
        @self.bot.tree.command(name='pr_comments', description='View pull request comments', guild=guild)
        @app_commands.describe(pr_url='Pull request URL')
        async def pr_comments_cmd(interaction: discord.Interaction, pr_url: Optional[str] = None):
            cmd = f'/pr_comments {pr_url}' if pr_url else '/pr_comments'
            await self.run_claude_slash_command(interaction, cmd)
        
        @self.bot.tree.command(name='vim', description='Enter vim mode in Claude', guild=guild)
        async def vim_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/vim')
        
        @self.bot.tree.command(name='help', description='Get Claude usage help', guild=guild)
        async def help_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/help')
        
        @self.bot.tree.command(name='doctor', description='Check Claude Code installation health', guild=guild)
        async def doctor_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/doctor')
    
    async def run_claude_slash_command(self, interaction: discord.Interaction, command: str):
        """Execute a Claude slash command and return the result"""
        await interaction.response.defer()
        
        try:
            # For slash commands, we need to echo the command to Claude's stdin
            process = subprocess.Popen(
                ['claude'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.expanduser('~')
            )
            
            stdout, stderr = process.communicate(input=command, timeout=30)
            response = stdout or stderr or "Command executed"
            
            # Format response
            embed = discord.Embed(
                title=f"Claude: {command}",
                description=f"```\n{response[:4000]}\n```" if response else "✅ Done",
                color=discord.Color.green() if process.returncode == 0 else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            await interaction.followup.send(embed=embed)
            
        except subprocess.TimeoutExpired:
            await interaction.followup.send("⏱️ Command timed out")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    async def request_permission(self, agent_name, action, context=""):
        """Send permission request to Discord and wait for response"""
        if not hasattr(self, 'channel'):
            return None
        
        embed = discord.Embed(
            title=f"🤖 Agent Permission Request",
            description=f"**Agent:** {agent_name}\n**Action:** {action}",
            color=discord.Color.yellow(),
            timestamp=datetime.now()
        )
        
        if context:
            embed.add_field(name="Context", value=context, inline=False)
        
        class PermissionView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)
                self.value = None
            
            @discord.ui.button(label='Approve', style=discord.ButtonStyle.success, emoji='✅')
            async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message('✅ Approved', ephemeral=True)
                self.value = 'yes'
                self.stop()
            
            @discord.ui.button(label='Deny', style=discord.ButtonStyle.danger, emoji='❌')
            async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message('❌ Denied', ephemeral=True)
                self.value = 'no'
                self.stop()
            
            @discord.ui.button(label='Skip', style=discord.ButtonStyle.secondary, emoji='⏭️')
            async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message('⏭️ Skipped', ephemeral=True)
                self.value = 'skip'
                self.stop()
        
        view = PermissionView()
        message = await self.channel.send(embed=embed, view=view)
        
        await view.wait()
        
        if view.value:
            embed.color = discord.Color.green() if view.value == 'yes' else discord.Color.red()
            embed.add_field(name="Decision", value=view.value.upper(), inline=False)
            await message.edit(embed=embed, view=None)
        
        return view.value
    
    def run(self):
        self.bot.run(self.token)


if __name__ == "__main__":
    config_file = os.path.expanduser("~/.claude/discord_config.json")
    
    if not os.path.exists(config_file):
        print("Please create ~/.claude/discord_config.json with:")
        print(json.dumps({
            "token": "YOUR_BOT_TOKEN",
            "channel_id": "YOUR_CHANNEL_ID",
            "guild_id": "YOUR_SERVER_ID"
        }, indent=2))
        exit(1)
    
    with open(config_file) as f:
        config = json.load(f)
    
    # Ensure guild_id exists for slash commands
    if 'guild_id' not in config:
        print("Please add 'guild_id' to your discord_config.json")
        print("Right-click your server name in Discord and Copy Server ID")
        exit(1)
    
    bridge = ClaudeDiscordBridge(config['token'], config['channel_id'], config['guild_id'])
    bridge.run()