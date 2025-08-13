#!/usr/bin/env python3

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import subprocess
import json
import os
import yaml
from datetime import datetime
from typing import Optional
from pathlib import Path

class ClaudeDiscordBridge:
    def __init__(self, token, channel_id, guild_id):
        self.token = token
        self.channel_id = int(channel_id)
        self.guild_id = int(guild_id)
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=self.intents)
        self.custom_commands = {}
        
        self.load_custom_commands()
        self.setup_handlers()
        self.setup_slash_commands()
    
    def load_custom_commands(self):
        """Load custom commands from ~/.claude/commands/"""
        commands_dir = Path.home() / '.claude' / 'commands'
        
        if not commands_dir.exists():
            print(f"Commands directory not found: {commands_dir}")
            return
        
        for cmd_file in commands_dir.glob('*.md'):
            try:
                with open(cmd_file, 'r') as f:
                    content = f.read()
                    
                    # Parse YAML frontmatter
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            frontmatter = yaml.safe_load(parts[1])
                            
                            cmd_name = frontmatter.get('name', cmd_file.stem)
                            description = frontmatter.get('description', f'Custom command: {cmd_name}')
                            
                            # Store command info
                            self.custom_commands[cmd_name] = {
                                'description': description[:100],  # Discord limit
                                'file': cmd_file.name,
                                'model': frontmatter.get('model'),
                                'allowed_tools': frontmatter.get('allowed-tools', [])
                            }
                            
                            print(f"Loaded custom command: /{cmd_name}")
                    
            except Exception as e:
                print(f"Error loading {cmd_file}: {e}")
    
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
        
        # Dynamic custom commands
        @self.bot.tree.command(name='custom', description='Run a custom Claude command', guild=guild)
        @app_commands.describe(
            command='The custom command to run',
            args='Arguments for the command'
        )
        @app_commands.choices(command=[
            app_commands.Choice(name=cmd, value=cmd) 
            for cmd in list(self.custom_commands.keys())[:25]  # Discord limit
        ])
        async def custom_cmd(interaction: discord.Interaction, command: str, args: Optional[str] = None):
            if command not in self.custom_commands:
                await interaction.response.send_message(f"❌ Unknown command: {command}")
                return
            
            await interaction.response.defer()
            
            try:
                # Build the command
                claude_cmd = f"/{command}"
                if args:
                    claude_cmd += f" {args}"
                
                # Execute via Claude
                process = subprocess.Popen(
                    ['claude'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.expanduser('~')
                )
                
                stdout, stderr = process.communicate(input=claude_cmd, timeout=120)
                response = stdout or stderr or "Command executed"
                
                # Create embed with command info
                cmd_info = self.custom_commands[command]
                embed = discord.Embed(
                    title=f"/{command}" + (f" {args}" if args else ""),
                    description=cmd_info['description'],
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                if cmd_info.get('model'):
                    embed.add_field(name="Model", value=cmd_info['model'], inline=True)
                
                # Add response
                if len(response) > 4000:
                    embed.add_field(name="Output", value="```\n" + response[:1000] + "\n...(truncated)```", inline=False)
                    await interaction.followup.send(embed=embed)
                    
                    # Send full response in chunks
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await interaction.channel.send(f"```\n{chunk}\n```")
                else:
                    embed.add_field(name="Output", value=f"```\n{response}```", inline=False)
                    await interaction.followup.send(embed=embed)
                
            except subprocess.TimeoutExpired:
                await interaction.followup.send("⏱️ Command timed out")
            except Exception as e:
                await interaction.followup.send(f"❌ Error: {str(e)}")
        
        # List available custom commands
        @self.bot.tree.command(name='commands', description='List all available custom commands', guild=guild)
        async def list_commands(interaction: discord.Interaction):
            if not self.custom_commands:
                await interaction.response.send_message("No custom commands found")
                return
            
            embed = discord.Embed(
                title="📋 Available Custom Commands",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            for cmd_name, cmd_info in self.custom_commands.items():
                value = cmd_info['description']
                if cmd_info.get('model'):
                    value += f"\n*Model: {cmd_info['model']}*"
                
                embed.add_field(
                    name=f"/{cmd_name}",
                    value=value,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        
        # Reload custom commands
        @self.bot.tree.command(name='reload', description='Reload custom commands from disk', guild=guild)
        async def reload_commands(interaction: discord.Interaction):
            old_count = len(self.custom_commands)
            self.custom_commands.clear()
            self.load_custom_commands()
            new_count = len(self.custom_commands)
            
            embed = discord.Embed(
                title="🔄 Commands Reloaded",
                description=f"Loaded {new_count} custom commands (was {old_count})",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Re-sync commands if needed
            try:
                guild = discord.Object(id=self.guild_id)
                await self.bot.tree.sync(guild=guild)
            except:
                pass
        
        # Standard Claude slash commands
        @self.bot.tree.command(name='clear', description='Clear Claude conversation history', guild=guild)
        async def clear_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/clear')
        
        @self.bot.tree.command(name='status', description='View Claude status', guild=guild)
        async def status_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/status')
        
        @self.bot.tree.command(name='cost', description='Show token usage', guild=guild)
        async def cost_cmd(interaction: discord.Interaction):
            await self.run_claude_slash_command(interaction, '/cost')
        
        @self.bot.tree.command(name='model', description='Change AI model', guild=guild)
        @app_commands.describe(model='Model to switch to')
        async def model_cmd(interaction: discord.Interaction, model: Optional[str] = None):
            cmd = f'/model {model}' if model else '/model'
            await self.run_claude_slash_command(interaction, cmd)
        
        @self.bot.tree.command(name='agents', description='Manage agents', guild=guild)
        @app_commands.describe(action='list, create, or agent name')
        async def agents_cmd(interaction: discord.Interaction, action: Optional[str] = None):
            cmd = f'/agents {action}' if action else '/agents'
            await self.run_claude_slash_command(interaction, cmd)
        
        # Quick access to common custom commands (if they exist)
        if 'gad' in self.custom_commands:
            @self.bot.tree.command(name='gad', description=self.custom_commands['gad']['description'], guild=guild)
            @app_commands.describe(query='Architecture question or design topic')
            async def gad_cmd(interaction: discord.Interaction, query: str):
                await self.run_custom_command(interaction, 'gad', query)
        
        if 'god' in self.custom_commands:
            @self.bot.tree.command(name='god', description=self.custom_commands['god']['description'], guild=guild)
            @app_commands.describe(task='Go implementation task')
            async def god_cmd(interaction: discord.Interaction, task: str):
                await self.run_custom_command(interaction, 'god', task)
        
        if 'feat' in self.custom_commands:
            @self.bot.tree.command(name='feat', description=self.custom_commands['feat']['description'], guild=guild)
            @app_commands.describe(feature='Feature to design')
            async def feat_cmd(interaction: discord.Interaction, feature: str):
                await self.run_custom_command(interaction, 'feat', feature)
    
    async def run_custom_command(self, interaction: discord.Interaction, cmd_name: str, args: str):
        """Execute a custom command"""
        await interaction.response.defer()
        
        try:
            claude_cmd = f"/{cmd_name} {args}" if args else f"/{cmd_name}"
            
            process = subprocess.Popen(
                ['claude'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.expanduser('~')
            )
            
            stdout, stderr = process.communicate(input=claude_cmd, timeout=120)
            response = stdout or stderr or "Command executed"
            
            if len(response) > 1900:
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                await interaction.followup.send(f"**/{cmd_name}**\n```\n{chunks[0]}\n```")
                for chunk in chunks[1:]:
                    await interaction.channel.send(f"```\n{chunk}\n```")
            else:
                await interaction.followup.send(f"**/{cmd_name}**\n```\n{response}\n```")
                
        except subprocess.TimeoutExpired:
            await interaction.followup.send("⏱️ Command timed out")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    async def run_claude_slash_command(self, interaction: discord.Interaction, command: str):
        """Execute a Claude slash command"""
        await interaction.response.defer()
        
        try:
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
    
    if 'guild_id' not in config:
        print("Please add 'guild_id' to your discord_config.json")
        exit(1)
    
    # Install PyYAML if needed
    try:
        import yaml
    except ImportError:
        print("Installing PyYAML...")
        subprocess.run(['pip', 'install', 'pyyaml'])
        import yaml
    
    bridge = ClaudeDiscordBridge(config['token'], config['channel_id'], config['guild_id'])
    bridge.run()