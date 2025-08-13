#!/usr/bin/env python3

import discord
from discord.ext import commands
import asyncio
import subprocess
import json
import os
from datetime import datetime
from typing import Optional

class ClaudeDiscordBridge:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = int(channel_id)
        self.pending_permissions = {}
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=self.intents)
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.bot.event
        async def on_ready():
            print(f'Discord bot connected as {self.bot.user}')
            self.channel = self.bot.get_channel(self.channel_id)
        
        @self.bot.command(name='claude')
        async def claude_prompt(ctx, *, prompt):
            """Send a prompt to Claude from Discord: !claude <your prompt>"""
            if ctx.channel.id != self.channel_id:
                return
            
            await ctx.message.add_reaction('⏳')
            
            # Execute Claude command locally
            try:
                result = subprocess.run(
                    ['claude', prompt],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                response = result.stdout or result.stderr
                
                # Split long responses
                if len(response) > 1900:
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await ctx.send(f"```\n{chunk}\n```")
                else:
                    await ctx.send(f"```\n{response}\n```")
                
                await ctx.message.remove_reaction('⏳', self.bot.user)
                await ctx.message.add_reaction('✅')
                
            except subprocess.TimeoutExpired:
                await ctx.send("⏱️ Command timed out")
                await ctx.message.add_reaction('❌')
            except Exception as e:
                await ctx.send(f"❌ Error: {str(e)}")
                await ctx.message.add_reaction('❌')
        
        @self.bot.command(name='status')
        async def status(ctx):
            """Check Claude status"""
            if ctx.channel.id != self.channel_id:
                return
            
            # Check if Claude is running
            result = subprocess.run(['pgrep', '-f', 'claude'], capture_output=True)
            if result.returncode == 0:
                await ctx.send("🟢 Claude is running")
            else:
                await ctx.send("🔴 Claude is not running")
    
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
        
        # Create view with buttons
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
        
        # Wait for response
        await view.wait()
        
        # Update embed with decision
        if view.value:
            embed.color = discord.Color.green() if view.value == 'yes' else discord.Color.red()
            embed.add_field(name="Decision", value=view.value.upper(), inline=False)
            await message.edit(embed=embed, view=None)
        
        return view.value
    
    async def send_notification(self, title, message, color=discord.Color.blue()):
        """Send a notification to Discord"""
        if not hasattr(self, 'channel'):
            return
        
        embed = discord.Embed(
            title=title,
            description=message,
            color=color,
            timestamp=datetime.now()
        )
        
        await self.channel.send(embed=embed)
    
    def run(self):
        self.bot.run(self.token)


# Helper script for agents to use
async def request_discord_permission(agent_name, action, context=""):
    """Helper function for agents to request permission via Discord"""
    config_file = os.path.expanduser("~/.claude/discord_config.json")
    
    if not os.path.exists(config_file):
        print("Discord not configured")
        return None
    
    with open(config_file) as f:
        config = json.load(f)
    
    bridge = ClaudeDiscordBridge(config['token'], config['channel_id'])
    
    # Run bot and request permission
    async def get_permission():
        await bridge.bot.wait_until_ready()
        result = await bridge.request_permission(agent_name, action, context)
        await bridge.bot.close()
        return result
    
    # Start bot in background
    bot_task = asyncio.create_task(bridge.bot.start(config['token']))
    perm_task = asyncio.create_task(get_permission())
    
    result = await perm_task
    bot_task.cancel()
    
    return result


if __name__ == "__main__":
    # Load config
    config_file = os.path.expanduser("~/.claude/discord_config.json")
    
    if not os.path.exists(config_file):
        print("Please create ~/.claude/discord_config.json with:")
        print(json.dumps({"token": "YOUR_BOT_TOKEN", "channel_id": "YOUR_CHANNEL_ID"}, indent=2))
        exit(1)
    
    with open(config_file) as f:
        config = json.load(f)
    
    bridge = ClaudeDiscordBridge(config['token'], config['channel_id'])
    bridge.run()