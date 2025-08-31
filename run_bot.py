#!/usr/bin/env python3
"""
Script to run the SteamXQuality Discord Bot.
Ensures the bot runs from the correct directory with proper Python path setup.
"""

import os
import sys
from pathlib import Path

def main():
    """Run the Discord bot from the correct directory."""
    # Ensure we're in the project root
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)
    
    # Add project root to Python path
    sys.path.insert(0, str(project_root))
    
    print(f"🚀 Starting SteamXQuality Discord Bot...")
    print(f"📁 Working directory: {project_root}")
    print(f"🐍 Python path includes: {project_root}")
    
    # Import and run the bot
    try:
        from bot.bot import run_bot
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
