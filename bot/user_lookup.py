"""
Discord user lookup utilities for SteamXQuality bot.
Handles finding Discord users from names using backend data.
"""

import logging
from typing import Optional
import nextcord

logger = logging.getLogger(__name__)

# Bot reference (will be set by main bot file)
bot = None


def set_bot_reference(bot_instance):
    """Set the bot reference for user lookup functions."""
    global bot
    bot = bot_instance


async def get_discord_username_from_name(person_name: str, role_type: str) -> Optional[str]:
    """Get Discord username from person name using the backend."""
    try:
        from backend.sheets_api import find_person
        import json
        
        # Use the new find_person function that searches all departments
        result = find_person(person_name)
        person_data = json.loads(result)
        
        if "error" not in person_data:
            discord_username = person_data.get("discord", "").strip()
            if discord_username:
                logger.info(f"🔍 Found Discord username: {person_name} → {discord_username} ({person_data.get('department', 'Unknown')})")
                return discord_username
            else:
                logger.warning(f"⚠️  No Discord username in profile for {person_name}")
                return None
        else:
            logger.warning(f"⚠️  Person not found: {person_name}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error getting Discord username for {person_name}: {e}")
        return None


async def get_user_by_username(discord_username: str) -> Optional[nextcord.Member]:
    """Get Discord user object by username from server members."""
    try:
        # Get the first guild (server) the bot is in
        if not bot:
            logger.error("❌ Bot reference not initialized")
            return None
            
        guild = bot.guilds[0] if bot.guilds else None
        if not guild:
            logger.error("❌ Bot is not in any guilds")
            return None
            
        # Search through server members for the username
        for member in guild.members:
            if member.name.lower() == discord_username.lower() or member.display_name.lower() == discord_username.lower():
                return member
                
        return None
        
    except Exception as e:
        logger.error(f"❌ Error finding user by username {discord_username}: {e}")
        return None
