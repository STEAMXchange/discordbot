"""
Quality Control Discord Bot - Main file with modular command structure.
"""

import asyncio
import os
import re
import io
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse

import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Thread, Embed
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

import sheets
from utils import BotUtils
from qc_helpers import (
    extract_text_and_fonts, map_fonts, categorize_text, 
    calculate_score, EXPECTED_FONTS, EXPECTED_COLORS, CANVA_FONT_ID
)

# Load environment variables
load_dotenv()

# Environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID", 1333405556714504242))
QC_ROLE_ID = int(os.getenv("QC_ROLE_ID", 1333429556429721674))
OWNER_USER_ID = int(os.getenv("OWNER_USER_ID", 0))
PASS_TAG_ID = int(os.getenv("PASS_TAG_ID", 1333406922098868326))
FAIL_TAG_ID = int(os.getenv("FAIL_TAG_ID", 1333406950955810899))
STALLED_TAG_ID = int(os.getenv("STALLED_TAG_ID", 1355469672278917264))

# Validate required environment variables
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is required")

# Set up bot with command intents
intents = nextcord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.messages = True
bot = commands.Bot(intents=intents)

# Initialize utils
utils = BotUtils(bot)

# Import and register commands
def setup_commands():
    """Import and setup all command modules."""
    from commands import (
        register, unregister, status, getprojectid, 
        whereisproject, geturl, getprojectinfo, mark, qc, palette, about, kill
    )
    
    # Register all commands
    register.setup(bot, utils)
    unregister.setup(bot, utils)
    status.setup(bot, utils)
    getprojectid.setup(bot, utils)
    whereisproject.setup(bot, utils)
    geturl.setup(bot, utils)
    getprojectinfo.setup(bot, utils)
    mark.setup(bot, utils)
    qc.setup(bot, utils)
    palette.setup(bot, utils)
    about.setup(bot, utils)
    kill.setup(bot, utils, OWNER_USER_ID)


async def auto_fail_expired_threads():
    """Auto-fail threads that are over 30 days old."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        db = utils.load_db()
        to_remove = []

        for thread_id, info in db.items():
            try:
                timestamp = datetime.fromisoformat(info["timestamp"])
                age_days = (datetime.utcnow() - timestamp).days

                if age_days >= 30:
                    project_id = info["project_id"]
                    print(f"[AUTO-FAIL] Thread {thread_id} | Project #{project_id} is over 30 days old")

                    # Try to fetch the thread
                    try:
                        thread = await bot.fetch_channel(int(thread_id))
                        await thread.edit(archived=True, locked=True, applied_tags=[])

                        # Apply "FAIL" tag + "Stalled" tag
                        await thread.edit(applied_tags=[
                            nextcord.ForumTag(id=FAIL_TAG_ID),  # FAIL
                            nextcord.ForumTag(id=STALLED_TAG_ID)   # STALLED
                        ])
                        await thread.send("🕒 This post was automatically marked as **FAIL (STALLED)** after 30 days of inactivity.")

                    except Exception as e:
                        print(f"[WARN] Could not edit thread {thread_id}: {e}")

                    sheets.markQCResult(project_id, "FAIL", "STALLED / Didn't fix")
                    to_remove.append(thread_id)

            except Exception as e:
                print(f"[ERROR] While processing thread {thread_id}: {e}")

        for tid in to_remove:
            del db[tid]

        utils.save_db(db)
        await asyncio.sleep(86400)  # Check daily


@bot.event
async def on_ready():
    """Bot ready event."""
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(auto_fail_expired_threads())


@bot.event
async def on_thread_create(thread: Thread):
    """Detects new forum posts in a specific channel and checks for Canva URLs and attachments."""
    if thread.parent_id != FORUM_CHANNEL_ID:
        return  # Ignore if not in the specific forum channel

    # Wait for a moment to ensure messages are available
    await asyncio.sleep(2)

    # Get the first message (original post)
    async for message in thread.history(limit=1, oldest_first=True):
        # If the user includes the override keyword, skip QC and ping the QC role for manual review
        if "|| --OVERRIDE ||" in message.content:
            report = f"**OVERRIDE**: Quality Control process skipped. Manual QC required for this post. {message.author.mention}"
            await thread.send(report)
            await thread.send(f"<@&{QC_ROLE_ID}> Review requested by {message.author.mention}")
            return  # Exit after sending the override message
        
        # Check if there is any attachment
        if not message.attachments:
            await thread.send(f"Invalid post: Missing thumbnail. {message.author.mention}")
            await thread.send(f"Deleting in 5 seconds...")
            await asyncio.sleep(5)
            await thread.delete()
            return

        # Get ProjectId
        # Normalize and extract project ID directly from message
        content = message.content.lower()
        project_id_match = re.search(r'(?:projectid\s*[:\s]*)?#?(\d{6})', content)
        project_id = project_id_match.group(1) if project_id_match else None

        if not project_id:
            await thread.send(f"Invalid post: Missing ProjectID. {message.author.mention}")
            await thread.send(f"Include a projectId:#YOURID or similar.")
            await thread.send(f"Deleting in 5 seconds...")
            await asyncio.sleep(5)
            await thread.delete()            
            return

        #Check if its a VALID project_id
        if not sheets.projectExists(project_id):
            await thread.send(f"Project does not exist!")
            await thread.send(f"Did you type the project id correctly?")
            await thread.send(f"Deleting in 5 seconds...")
            await asyncio.sleep(5)
            await thread.delete()
            return

        # Check if project is already finished
        if sheets.isProjectDone(project_id):
            await thread.send(f"Project already finished!")
            await thread.send(f"If you think this is an error, contact a higher up.")
            await thread.send(f"Deleting in 5 seconds...")
            await asyncio.sleep(5)
            await thread.delete()
            return

        # Check author's department
        department = sheets.getDepartmentFromDiscord(message.author.name)
        print(f"{message.author.name}'s Department: {department}")
        if department not in ["Management", "Quality Control", "Designers"]:
            await thread.send(f"Insufficient permissions, {message.author.mention}.")
            await thread.send(f"Contact a higher up if you wish to apply as a designer.")
            await thread.send(f"Deleting in 5 seconds...")
            await asyncio.sleep(5)
            await thread.delete()
            return

        # Check if the person POSTING IS the designer. if not wtf are you doing
        designer = sheets.getDesignerFromProjectID(project_id)
        if not designer:
            await thread.send(f"FATAL ERROR: No designer assigned for Project #{project_id}.")
            await thread.send(f"Deleting in 5 seconds...")
            await asyncio.sleep(5)
            await thread.delete()
            return

        designer_discord = sheets.getDiscordUsername(designer)
        print(f"Designer's Discord: {designer_discord}")
        if not designer_discord:
            await thread.send(f"FATAL ERROR: {designer} NOT IN CONTACT DIRECTORY.")
            await thread.send(f"Deleting in 5 seconds...")
            await asyncio.sleep(5)
            await thread.delete()
            return
        
        if not designer_discord == message.author.name:
            await thread.send(f"You are not the designer for projectID (#{project_id}). {message.author.mention}")
            await thread.send(f"Please get {designer_discord} to post themselves.")
            await thread.send(f"Deleting in 5 seconds...")
            await asyncio.sleep(5)
            await thread.delete()
            return
    
        # Check for a Canva URL in the message
        canva_url = re.search(r"(https?://www\.canva\.com/design/[^\s]+)", message.content)

        if not canva_url:
            await thread.send(f"WARNING: Missing Canva link. {message.author.mention}")
            await thread.send(f"Manual QC required. <@&{QC_ROLE_ID}>")
            return  # Exit if no Canva link found

        url = canva_url.group(1)

        # Extract the core Canva URL without query parameters
        parsed_url = urlparse(url)
        core_url = urlunparse(parsed_url._replace(query=''))

        # Check if the URL ends with `/edit`, change it to `/view`
        if core_url.endswith("/edit"):
            core_url = core_url.replace("/edit", "/view")
            print(f"Modified URL to: {core_url}")
        
        print(f"Found Canva URL: {core_url}")
        
        # Run the quality control check
        extracted_data = extract_text_and_fonts(core_url)
        final_data = map_fonts(extracted_data["text_data"], extracted_data["fonts"])
        categorized_text = categorize_text(final_data)

        total_score = 0
        total_possible_score = 0
        report = f"Quality Control Report for {message.author.name}\n"

        for category, items in categorized_text.items():
            report += f"\n{category}:\n"
            for item, font_name in items:
                expected_font = EXPECTED_FONTS.get(category, "Unknown")
                expected_color = EXPECTED_COLORS.get(category, "Unknown")
                match_status = "✅" if font_name == expected_font else "❌"
                score = calculate_score(font_name, expected_font, item['color'], expected_color)
                total_score += score
                total_possible_score += 10

                report += f"• `{item['text']}` ({item['size']}px) | Font: {font_name} {match_status}\n"

        final_score = (total_score / total_possible_score) * 100 if total_possible_score else 0
        report += f"\nFinal Score: {final_score:.2f}/100 🎯"

        # Final raw report with no markdown
        report += f"\nPROJECT ID: {project_id}"

        # Send short summary first
        await thread.send(f"📄 Quality Control report for {message.author.mention}")

        # Attach full report as .txt file
        report_file = io.BytesIO(report.encode("utf-8"))
        await thread.send(file=nextcord.File(report_file, filename=f"qc_report_{project_id}.txt"))

        # Send Canva link + reminder
        await thread.send(f"🔗 Canva URL: {core_url}\n⚠️ THIS IS NOT A FINAL REPORT. MANUAL QC IS REQUIRED.")
        
        await thread.send(f"<@&{QC_ROLE_ID}> Review requested by {message.author.mention}")

        #MARK AS DONE
        sheets.markDesignerDone(project_id, core_url, thread.jump_url)

        #REGISTER
        utils.register_thread(str(thread.id), project_id, message.author.name)
        print(f"✅ Auto-registered thread {thread.id} to project {project_id}")


@bot.event
async def on_thread_delete(thread: Thread):
    """Handle thread deletion."""
    thread_id = str(thread.id)
    if utils.unregister_thread(thread_id):
        print(f"🗑️ Auto-unregistered thread {thread_id}")


if __name__ == "__main__":
    # Setup commands
    setup_commands()
    
    # Run the bot
    bot.run(DISCORD_BOT_TOKEN)
