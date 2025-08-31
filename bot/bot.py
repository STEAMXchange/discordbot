"""
Quality Control Discord Bot - Main file with modular command structure.
"""

import os
import sys
from pathlib import Path
from typing import Optional
import logging

import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv

# Add project root to Python path (more robust path resolution)
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import timers
try:
    from . import timers
except ImportError:
    import timers

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Environment variables
DISCORD_BOT_TOKEN: Optional[str] = os.getenv("DISCORD_BOT_TOKEN")
FORUM_CHANNEL_ID: int = int(os.getenv("FORUM_CHANNEL_ID", 1333405556714504242))
QC_ROLE_ID: int = int(os.getenv("QC_ROLE_ID", 1333429556429721674))
OWNER_USER_ID: int = int(os.getenv("OWNER_USER_ID", 0))
PASS_TAG_ID: int = int(os.getenv("PASS_TAG_ID", 1333406922098868326))
FAIL_TAG_ID: int = int(os.getenv("FAIL_TAG_ID", 1333406950955810899))
STALLED_TAG_ID: int = int(os.getenv("STALLED_TAG_ID", 1355469672278917264))

# Validate required environment variables
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is required")

# Set up bot with command intents
intents: nextcord.Intents = nextcord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.messages = True
bot: commands.Bot = commands.Bot(intents=intents)

@bot.event
async def on_ready() -> None:
    """Called when the bot is ready."""
    print(f"🤖 {bot.user} is now online!")
    print(f"📊 Connected to {len(bot.guilds)} guilds")
    
    # Initialize and start timers
    timers.setup_timers(bot)
    print("🚀 All timers started successfully!")

def run_bot() -> None:
    """Run the Discord bot."""
    # Run the bot
    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)
    else:
        print("ERROR: DISCORD_BOT_TOKEN not found in environment variables")


if __name__ == "__main__":
    run_bot()
