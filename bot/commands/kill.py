"""
Kill command - Safely terminates the bot (admin only).
"""

import asyncio
import sys
from typing import Any, Optional
from nextcord import Interaction


def setup(bot: Any, utils: Any, owner_user_id: Optional[int] = None) -> None:
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="kill", description="Safely terminate the bot (admin only).")
    async def kill(interaction: Interaction) -> None:
        # Check if user has admin permissions OR is the owner
        if not (interaction.user.guild_permissions.administrator or (owner_user_id and interaction.user.id == owner_user_id)):
            await interaction.response.send_message(
                "❌ **Access Denied**\n"
                "This command requires administrator permissions.",
                ephemeral=True
            )
            return
        
        # Confirm the shutdown
        await interaction.response.send_message(
            "🔴 **Bot Shutdown Initiated**\n"
            f"Requested by: {interaction.user.mention}\n"
            "The bot will terminate in 3 seconds...",
            ephemeral=False
        )
        
        print(f"[SHUTDOWN] Bot shutdown requested by {interaction.user.name} ({interaction.user.id})")
        
        # Give a moment for the message to send
        await asyncio.sleep(3)
        
        # Log the shutdown
        print("[SHUTDOWN] Bot is shutting down...")
        
        # Close the bot connection gracefully
        await bot.close()
        
        # Exit the program
        sys.exit(0)
