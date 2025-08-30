#!/usr/bin/env python3
"""
🤖 SteamXQuality Bot Development Test Playground
=================================================

This is your development playground for testing bot functionality.
Perfect for testing Discord bot components without running the full bot.

Usage:
    python bot/test.py                  # Run interactive playground
    python -i bot/test.py               # Start Python REPL with everything loaded
    
Or import in your own scripts:
    from bot.test import *
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import bot utilities
try:
    from bot.utils import BotUtils, QC_ROLE_ID, FORUM_CHANNEL_ID, PASS_TAG_ID, FAIL_TAG_ID
    from bot.qc_helpers import (
        CANVA_FONT_ID, EXPECTED_FONTS, EXPECTED_COLORS,
        normalize_font_id, calculate_score
    )
    
    print("✅ Bot imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root or have proper PYTHONPATH")
    sys.exit(1)


# 🎮 PLAYGROUND FUNCTIONS
def demo_bot_utils():
    """Demonstrate bot utility functions."""
    print("\n🔧 === BOT UTILITIES DEMO ===")
    
    # Mock bot object for testing
    class MockBot:
        def __init__(self):
            self.guilds = []
    
    # Create utils instance
    mock_bot = MockBot()
    utils = BotUtils(mock_bot)
    
    print(f"\n📋 Bot Configuration:")
    print(f"  QC Role ID: {QC_ROLE_ID}")
    print(f"  Forum Channel ID: {FORUM_CHANNEL_ID}")
    print(f"  Pass Tag ID: {PASS_TAG_ID}")
    print(f"  Fail Tag ID: {FAIL_TAG_ID}")
    
    # Test project ID cleaning
    print(f"\n🧹 Project ID Cleaning:")
    test_ids = ["#123456", "123456", "#000001", "1"]
    for pid in test_ids:
        cleaned = utils.clean_project_id(pid)
        print(f"  {pid:>8} → {cleaned}")
    
    # Test thread database operations
    print(f"\n💾 Thread Database Operations:")
    thread_id = "12345678901234567890"
    project_id = "000001"
    user = "TestUser"
    
    # Register thread
    utils.register_thread(thread_id, project_id, user)
    print(f"  ✅ Registered thread {thread_id} to project {project_id}")
    
    # Get thread info
    info = utils.get_thread_project(thread_id)
    if info:
        print(f"  📋 Thread info: {info}")
    
    # Find project thread
    found_thread = utils.find_project_thread(project_id)
    print(f"  🔍 Found thread for project {project_id}: {found_thread}")
    
    # Unregister thread
    success = utils.unregister_thread(thread_id)
    print(f"  🗑️ Unregistered thread: {success}")
    
    return True


def demo_qc_helpers():
    """Demonstrate QC helper functions."""
    print("\n🎨 === QC HELPERS DEMO ===")
    
    print(f"\n🎯 Font Configuration:")
    print(f"  Canva Font IDs: {len(CANVA_FONT_ID)} fonts mapped")
    for font_id, font_name in CANVA_FONT_ID.items():
        print(f"    {font_id}: {font_name}")
    
    print(f"\n📝 Expected Fonts by Category:")
    for category, font in EXPECTED_FONTS.items():
        print(f"    {category:>12}: {font}")
    
    print(f"\n🎨 Expected Colors by Category:")
    for category, color in EXPECTED_COLORS.items():
        print(f"    {category:>12}: {color}")
    
    # Test font normalization
    print(f"\n🔧 Font ID Normalization:")
    test_font_ids = [
        '"YAFcfijbpbU", _fb_, auto',
        'YAFdtQJYBw 123',
        '"YACgEUFdPdA"'
    ]
    for font_id in test_font_ids:
        normalized = normalize_font_id(font_id)
        print(f"    {font_id:>25} → {normalized}")
    
    # Test scoring
    print(f"\n📊 QC Scoring Examples:")
    test_cases = [
        ("Grand Cru", "Grand Cru", "rgb(225, 232, 241)", "rgb(225, 232, 241)"),  # Perfect match
        ("Grand Cru", "Nunito Sans", "rgb(225, 232, 241)", "rgb(225, 232, 241)"),  # Wrong font
        ("Grand Cru", "Grand Cru", "rgb(255, 0, 0)", "rgb(225, 232, 241)"),  # Wrong color
        ("Arial", "Comic Sans", "rgb(255, 0, 0)", "rgb(0, 255, 0)"),  # Everything wrong
    ]
    
    for font_actual, font_expected, color_actual, color_expected in test_cases:
        score = calculate_score(font_actual, font_expected, color_actual, color_expected)
        print(f"    Font: {font_actual:>12} vs {font_expected:>12} | Color match | Score: {score}/10")
    
    return True


def demo_mock_discord_objects():
    """Create mock Discord objects for testing."""
    print("\n🎭 === MOCK DISCORD OBJECTS ===")
    
    class MockUser:
        def __init__(self, name: str, user_id: int):
            self.name = name
            self.id = user_id
            self.mention = f"<@{user_id}>"
            
        def __str__(self):
            return self.name
    
    class MockThread:
        def __init__(self, thread_id: int, name: str):
            self.id = thread_id
            self.name = name
            self.jump_url = f"https://discord.com/channels/guild/channel/{thread_id}"
    
    class MockMessage:
        def __init__(self, content: str, author: MockUser):
            self.content = content
            self.author = author
            self.attachments = []
    
    # Create mock objects
    user = MockUser("TestUser", 123456789)
    thread = MockThread(987654321, "Test QC Thread")
    message = MockMessage("ProjectID: #000001 https://canva.com/design/test", user)
    
    print(f"  👤 Mock User: {user.name} ({user.id})")
    print(f"  🧵 Mock Thread: {thread.name} ({thread.id})")
    print(f"  💬 Mock Message: {message.content[:50]}...")
    
    return {"user": user, "thread": thread, "message": message}


def test_thread_management():
    """Test thread management functionality."""
    print("\n🧵 === THREAD MANAGEMENT TEST ===")
    
    # Create utils instance
    class MockBot:
        pass
    
    utils = BotUtils(MockBot())
    
    # Test multiple thread operations
    test_data = [
        ("111111111111111111", "000001", "Alice"),
        ("222222222222222222", "000002", "Bob"),
        ("333333333333333333", "000003", "Charlie"),
    ]
    
    print(f"\n📝 Registering test threads:")
    for thread_id, project_id, user in test_data:
        utils.register_thread(thread_id, project_id, user)
        print(f"  ✅ Thread {thread_id[-6:]}... → Project {project_id} (by {user})")
    
    print(f"\n🔍 Looking up threads:")
    for thread_id, project_id, user in test_data:
        info = utils.get_thread_project(thread_id)
        found_thread = utils.find_project_thread(project_id)
        print(f"  📋 Project {project_id}: Thread {found_thread[-6:] if found_thread else 'None'}... (by {info['registered_by'] if info else 'None'})")
    
    print(f"\n🗑️ Cleaning up test threads:")
    for thread_id, project_id, user in test_data:
        success = utils.unregister_thread(thread_id)
        print(f"  {'✅' if success else '❌'} Unregistered {thread_id[-6:]}...")
    
    return True


def interactive_playground():
    """Start an interactive playground session."""
    print(f"\n🎮 === BOT INTERACTIVE PLAYGROUND ===")
    print(f"Available functions:")
    print(f"  • demo_bot_utils()")
    print(f"  • demo_qc_helpers()")
    print(f"  • demo_mock_discord_objects()")
    print(f"  • test_thread_management()")
    print(f"  • quick_test()")
    print(f"\nAvailable objects:")
    print(f"  • BotUtils class")
    print(f"  • CANVA_FONT_ID, EXPECTED_FONTS, EXPECTED_COLORS")
    print(f"  • QC_ROLE_ID, FORUM_CHANNEL_ID, PASS_TAG_ID, FAIL_TAG_ID")
    print(f"\nTry: quick_test() to run all demos")


def simulate_qc_workflow():
    """Simulate a complete QC workflow."""
    print(f"\n🔄 === QC WORKFLOW SIMULATION ===")
    
    # Mock bot and utils
    class MockBot:
        pass
    
    utils = BotUtils(MockBot())
    
    # Simulate workflow steps
    print(f"\n1️⃣ New thread created...")
    thread_id = "555555555555555555"
    project_id = "000123"
    user = "DesignerUser"
    
    print(f"2️⃣ Extracting project ID from message...")
    message_content = "Here's my design for ProjectID: #000123 https://canva.com/design/example"
    import re
    project_match = re.search(r'#?(\d{6})', message_content)
    extracted_id = project_match.group(1) if project_match else None
    print(f"   Extracted: {extracted_id}")
    
    print(f"3️⃣ Registering thread to project...")
    utils.register_thread(thread_id, project_id, user)
    
    print(f"4️⃣ Simulating QC process...")
    # Mock QC results
    qc_results = {
        "total_score": 85,
        "max_score": 100,
        "font_matches": 3,
        "color_matches": 2,
        "issues": ["Title font incorrect", "Body text color off"]
    }
    
    print(f"   📊 QC Score: {qc_results['total_score']}/{qc_results['max_score']}")
    print(f"   ✅ Font matches: {qc_results['font_matches']}")
    print(f"   🎨 Color matches: {qc_results['color_matches']}")
    print(f"   ⚠️ Issues: {', '.join(qc_results['issues'])}")
    
    print(f"5️⃣ QC completed, thread cleanup...")
    utils.unregister_thread(thread_id)
    
    print(f"✅ Workflow simulation complete!")
    return True


def quick_test():
    """Run a quick test of all bot functionality."""
    print("🤖 === QUICK TEST OF ALL BOT FUNCTIONALITY ===")
    
    results = []
    results.append(("Bot Utils", demo_bot_utils()))
    results.append(("QC Helpers", demo_qc_helpers()))
    results.append(("Thread Management", test_thread_management()))
    results.append(("QC Workflow", simulate_qc_workflow()))
    
    print(f"\n📊 === TEST RESULTS ===")
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:>20}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\n🎯 Overall: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("🎉 All bot systems operational! Ready for Discord!")
    else:
        print("⚠️ Some issues detected. Check your bot configuration.")


def main():
    """Main function when run as script."""
    print("🤖 SteamXQuality Bot Development Playground")
    print("=" * 50)
    
    # Check environment
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    if discord_token:
        print("✅ Discord bot token found in environment")
    else:
        print("⚠️ No Discord bot token found (DISCORD_BOT_TOKEN)")
    
    # Run quick test
    quick_test()
    
    # Start interactive mode
    print(f"\n🎮 Starting interactive playground...")
    print(f"Type 'interactive_playground()' for help, or 'quick_test()' to run all demos")
    
    # Keep Python session alive for interactive use
    import code
    code.interact(local=globals())


if __name__ == "__main__":
    main()
else:
    # When imported, just show what's available
    print("🤖 SteamXQuality Bot Test Playground Loaded!")
    print("Available functions: demo_bot_utils, demo_qc_helpers, test_thread_management")
    print("Try: quick_test() to run all demos")
