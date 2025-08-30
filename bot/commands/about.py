"""
About command - Shows version info and system details.
"""

import platform
import sys
from datetime import datetime
from typing import Any
import nextcord
from nextcord import Interaction, Embed


def setup(bot: Any, utils: Any) -> None:
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="about", description="Show bot version and system information.")
    async def about(interaction: Interaction) -> None:
        # Create an embed for better formatting
        embed: Embed = Embed(
            title="🤖 SteamXQuality Bot",
            description="Quality Control Discord Bot for STEAMXchange",
            color=0x00ff00
        )
        
        # Bot version info
        embed.add_field(
            name="📋 Bot Info",
            value=f"**Version:** 2.0.1\n"
                  f"**Author:** Areng\n"
                  f"**Framework:** nextcord {nextcord.__version__}",
            inline=False
        )
        
        # System info
        embed.add_field(
            name="💻 System Info",
            value=f"**OS:** {platform.system()} {platform.release()}\n"
                  f"**Python:** {sys.version.split()[0]}\n"
                  f"**Architecture:** {platform.architecture()[0]}",
            inline=False
        )
        
        # Bot stats
        guild_count: int = len(bot.guilds)
        user_count: int = sum(guild.member_count or 0 for guild in bot.guilds)
        
        embed.add_field(
            name="📊 Bot Stats",
            value=f"**Servers:** {guild_count}\n"
                  f"**Users:** {user_count}\n"
                  f"**Uptime:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False
        )

        embed.set_footer(text="Made with ❤️ for STEAMXchange")
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)
