

import asyncio
from datetime import datetime, timedelta
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Thread, SlashOption
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import io
import re
import time
from selenium import webdriver
from urllib.parse import urlparse, urlunparse
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sheets
import json
import os
import platform
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_FILE = "thread_db.json"
QC_ROLE_ID = int(os.getenv("QC_ROLE_ID", 1333429556429721674))
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

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

# Font ID mapping
CANVA_FONT_ID = {
    "YAFcfijbpbU": "Grand Cru",
    "YAFdtQJYBw": "Nunito Sans",
    "YACgEUFdPdA": "Libre Baskerville"
}

EXPECTED_FONTS = {
    "Title": "Grand Cru",
    "Subheading": "Libre Baskerville",
    "Body Text": "Nunito Sans"
}

EXPECTED_COLORS = {
    "Title": "rgb(225, 232, 241)",
    "Subheading": "rgb(225, 232, 241)",
    "Body Text": "rgb(225, 232, 241)"
}

# Forum Channel ID
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID", 1333405556714504242))

def extract_text_and_fonts(url: str):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Only apply Linux path override if needed
    if platform.system() == "Linux":
        options.binary_location = "/usr/bin/google-chrome"

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    time.sleep(2)

    script = """
    let data = { fonts: [], text_data: [] };

    let fontSet = new Set();
    performance.getEntriesByType("resource").forEach(resource => {
        if (resource.name.endsWith(".woff2")) {
            fontSet.add(resource.name);
        }
    });

    data.fonts = Array.from(fontSet);

    document.querySelectorAll('span.OYPEnA').forEach(el => { 
        let style = window.getComputedStyle(el);
        let textSize = parseFloat(style.fontSize);
        let color = style.color;
        let bgColor = style.backgroundColor;
        let fontID = style.fontFamily;
        let text = el.textContent.trim();

        if (text !== "" && textSize) {
            data.text_data.push({
                "text": text,
                "size": textSize,
                "color": color,
                "background": bgColor,
                "font_id": fontID
            });
        }
    });

    return data;
    """

    extracted_data = driver.execute_script(script)
    driver.quit()

    return extracted_data

def normalize_font_id(font_id):
    normalized_id = re.sub(r'\s*\d*', '', font_id)
    normalized_id = re.sub(r'\s*,\s*_fb_,\s*auto.*', '', normalized_id)
    return normalized_id.strip('"')

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

from datetime import datetime, timedelta

async def auto_fail_expired_threads():
    await bot.wait_until_ready()
    while not bot.is_closed():
        db = load_db()
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
                        fail_tag_id = int(os.getenv("FAIL_TAG_ID", 1333406950955810899))
                        stalled_tag_id = int(os.getenv("STALLED_TAG_ID", 1355469672278917264))
                        await thread.edit(applied_tags=[
                            nextcord.ForumTag(id=fail_tag_id),  # FAIL
                            nextcord.ForumTag(id=stalled_tag_id)   # STALLED
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

        save_db(db)
        await asyncio.sleep(86400)  # Check daily

def map_fonts(text_data, font_files):
    font_mapping = {}

    for url in font_files:
        match = re.search(r"/([^/]+)\.woff2", url)
        if match:
            font_id = match.group(1)
            font_mapping[font_id] = url

    for text_obj in text_data:
        font_match = None
        normalized_font_id = normalize_font_id(text_obj["font_id"])

        for font_id in font_mapping:
            if normalized_font_id in font_id:
                font_match = font_mapping[font_id]
                break

        text_obj["matched_font"] = font_match if font_match else "Unknown"

    return text_data

def categorize_text(final_data):
    categorized_data = {
        "Title": [],
        "Subheading": [],
        "Body Text": []
    }

    for item in final_data:
        size = item['size']
        font_name = CANVA_FONT_ID.get(normalize_font_id(item["font_id"]), "Unknown")

        if size >= 70:
            categorized_data["Title"].append((item, font_name))
        elif 40 <= size < 70:
            categorized_data["Subheading"].append((item, font_name))
        else:
            categorized_data["Body Text"].append((item, font_name))

    return categorized_data

def calculate_score(font_name, expected_font, color, expected_color):
    score = 0
    if font_name == expected_font:
        score += 5
    if color == expected_color:
        score += 5
    return score

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(auto_fail_expired_threads())

#MAIN LISTNER
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
            await thread.send(f"<@&1333429556429721674> Review requested by {message.author.mention}")
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
            await thread.send(f"Manual QC required. <@&1333429556429721674>")
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
        
        await thread.send(f"<@&1333429556429721674> Review requested by {message.author.mention}")

        #MARK AS DONE
        sheets.markDesignerDone(project_id, core_url, thread.jump_url)

        #REGISTER
        thread_id = str(thread.id)
        db = load_db()
        db[thread_id] = {
            "project_id": project_id,
            "registered_by": message.author.name,
            "timestamp": datetime.now().isoformat()
        }
        save_db(db)
        print(f"✅ Auto-registered thread {thread_id} to project {project_id}")

@bot.event
async def on_thread_delete(thread: Thread):
    thread_id = str(thread.id)
    db = load_db()

    if thread_id in db:
        del db[thread_id]
        save_db(db)
        print(f"🗑️ Auto-unregistered thread {thread_id}")

@bot.slash_command(name="getprojectinfo", description="Gets info about a projectID")
async def getProjectInfo(
    interaction: Interaction,
    project_id: str = SlashOption(description="Project ID like #000003")
):
    if project_id[0] == "#":
        project_id = project_id[1:]

    if not sheets.projectExists(project_id):
        await interaction.response.send_message(content=f"Project id: {project_id} not found!", ephemeral=True)
        return

    clean_id = project_id.strip().lstrip("#").zfill(6)
    row = sheets.getProjectRow(clean_id)

    if not row:
        await interaction.response.send_message(
            f"❌ Project ID `{project_id}` not found.",
            ephemeral=True
        )
        return

    embed = Embed(
        title=f"📄 Project Info: #{clean_id}",
        description=row.get(sheets.ProjectCols.DESCRIPTION, "No description."),
        color=0xB700FF
    )

    qc_result = row.get(sheets.ProjectCols.QC_PASSED, "N/A")
    qc_emoji = "✅" if qc_result.strip().upper() == "YES" else ("❌" if qc_result.strip().upper() == "NO" else "❓")

    embed.add_field(name="📌 Name", value=row.get(sheets.ProjectCols.NAME, "N/A"), inline=False)
    embed.add_field(name="👤 Author", value=row.get(sheets.ProjectCols.AUTHOR, "N/A"), inline=False)
    embed.add_field(name="🎨 Designer", value=row.get(sheets.ProjectCols.DESIGNER, "N/A"), inline=False)
    embed.add_field(name="✅ Done?", value=row.get(sheets.ProjectCols.DONE, "N/A"), inline=False)
    embed.add_field(name="🔍 QC Passed?", value=f"{qc_emoji} {qc_result}", inline=False)
    embed.add_field(name="🕒 Start Date", value=row.get(sheets.ProjectCols.START_DATE, "N/A"), inline=False)
    embed.add_field(name="📅 Due Date", value=row.get(sheets.ProjectCols.END_DATE, "N/A"), inline=False)
    embed.add_field(name="📝 Topic", value=row.get(sheets.ProjectCols.TOPIC, "N/A"), inline=False)
    embed.set_footer(text="Areng Management Project System")

    await interaction.response.send_message(embed=embed)


@bot.slash_command(name="register", description="Link this thread to a Project ID.")
async def register(interaction: Interaction, project_id: str = SlashOption(description="Project ID like #000003")):
    thread = interaction.channel

    if not isinstance(thread, Thread):
        await interaction.response.send_message(
            "❌ This command can only be used inside a thread.", ephemeral=True
        )
        return

    # Permissions: must have QC role or manage messages
    has_qc_role = next((r.id == QC_ROLE_ID for r in interaction.user.roles), False)
    has_manage_perm = interaction.user.guild_permissions.manage_messages

    if not has_qc_role and not has_manage_perm:
        await interaction.response.send_message(
            "🚫 You don't have permission to use this command.", ephemeral=True
        )
        return

    # Strip leading # and pad zeros if needed
    project_id = project_id.lstrip("#").zfill(6)

    # Validate project ID
    if not sheets.projectExists(project_id):
        await interaction.response.send_message(
            f"❌ Project ID `#{project_id}` does not exist.", ephemeral=True
        )
        return

    # Save to JSON DB
    thread_id = str(thread.id)
    db = load_db()
    db[thread_id] = {
        "project_id": project_id,
        "registered_by": interaction.user.name,
        "timestamp": datetime.now().isoformat()
    }
    save_db(db)

    await interaction.response.send_message(
        f"✅ Registered this thread to project `#{project_id}`."
    )

@bot.slash_command(name="getprojectid", description="Get the project ID linked to this thread")
async def getprojectid(interaction: Interaction):
    thread = interaction.channel
    
    if not isinstance(thread, Thread):
        await interaction.response.send_message("❌ This command can only be used inside a thread.", ephemeral=True)
        return
    
    db = load_db()
    thread_id = str(thread.id)
    
    if thread_id in db:
        project_id = db[thread_id]["project_id"]
        await interaction.response.send_message(f"📋 Project ID: `#{project_id}`", ephemeral=True)
    else:
        await interaction.response.send_message("❌ This thread is not registered to any project.", ephemeral=True)

@bot.slash_command(name="whereisproject", description="Find the thread/location of a project ID")
async def whereisproject(
    interaction: Interaction,
    project_id: str = SlashOption(description="Project ID like #000003")
):
    # Clean up the project ID
    clean_project_id = project_id.lstrip("#").zfill(6)
    
    # Check if project exists first
    if not sheets.projectExists(clean_project_id):
        await interaction.response.send_message(f"❌ Project `#{clean_project_id}` does not exist.", ephemeral=True)
        return
    
    # Search through the database
    db = load_db()
    found_thread_id = None
    
    for thread_id, info in db.items():
        if info["project_id"] == clean_project_id:
            found_thread_id = thread_id
            break
    
    if found_thread_id:
        try:
            thread = bot.get_channel(int(found_thread_id))
            if thread:
                await interaction.response.send_message(
                    f"📍 Project `#{clean_project_id}` is in thread: {thread.jump_url}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❓ Project `#{clean_project_id}` thread exists but couldn't be accessed.",
                    ephemeral=True
                )
        except:
            await interaction.response.send_message(
                f"❓ Project `#{clean_project_id}` thread exists but couldn't be accessed.",
                ephemeral=True
            )
    else:
        await interaction.response.send_message(
            f"❓ Project `#{clean_project_id}` exists but is not linked to any active thread.",
            ephemeral=True
        )

@bot.slash_command(name="status", description="Check which Project ID this thread is linked to.")
async def status(interaction: Interaction):
    thread = interaction.channel

    if not isinstance(thread, Thread):
        await interaction.response.send_message("❌ This command can only be used inside a thread.", ephemeral=True)
        return

    db = load_db()
    thread_id = str(thread.id)

    if thread_id in db:
        entry = db[thread_id]
        await interaction.response.send_message(
            f"✅ This thread is linked to Project `#{entry['project_id']}`\n"
            f"🔗 Registered by: `{entry['registered_by']}`\n"
            f"🕓 Registered at: `{entry['timestamp']}`"
        )
    else:
        await interaction.response.send_message("❌ This thread is not registered to any project.")

@bot.slash_command(name="getUrl", description="Get the Canva URL for this thread's project.")
async def canva(interaction: Interaction):
   thread = interaction.channel

   if not isinstance(thread, Thread):
       await interaction.response.send_message("❌ This command can only be used inside a thread.", ephemeral=True)
       return

   db = load_db()
   thread_id = str(thread.id)

   if thread_id not in db:
       await interaction.response.send_message("❌ This thread is not registered to any project.", ephemeral=True)
       return

   project_id = db[thread_id]['project_id']
   canva_url = getCanvaURL(project_id)

   if canva_url and canva_url != "IMAGE SENT IN QC CHAT":
       await interaction.response.send_message(f"🎨 Canva URL for Project `#{project_id}`: {canva_url}")
   elif canva_url == "IMAGE SENT IN QC CHAT":
       await interaction.response.send_message(f"📸 Project `#{project_id}`: Design was sent directly in QC chat (no Canva link)")
   else:
       await interaction.response.send_message(f"❌ No Canva URL found for Project `#{project_id}`")

@bot.slash_command(name="register", description="Link this thread to a Project ID.")
async def register(interaction: Interaction, project_id: str = SlashOption(description="Project ID like #000003")):
    thread = interaction.channel

    if not isinstance(thread, Thread):
        await interaction.response.send_message(
            "❌ This command can only be used inside a thread.", ephemeral=True
        )
        return

    # Permissions: must have QC role or manage messages
    has_qc_role = next((r.id == QC_ROLE_ID for r in interaction.user.roles), False)
    has_manage_perm = interaction.user.guild_permissions.manage_messages

    if not has_qc_role and not has_manage_perm:
        await interaction.response.send_message(
            "🚫 You don't have permission to use this command.", ephemeral=True
        )
        return

    # Strip leading # and pad zeros if needed
    project_id = project_id.lstrip("#").zfill(6)

    # Validate project ID
    if not sheets.projectExists(project_id):
        await interaction.response.send_message(
            f"❌ Project ID `#{project_id}` does not exist.", ephemeral=True
        )
        return

    # Save to JSON DB
    thread_id = str(thread.id)
    db = load_db()
    db[thread_id] = {
        "project_id": project_id,
        "registered_by": interaction.user.name,
        "timestamp": datetime.now().isoformat()
    }
    save_db(db)

    await interaction.response.send_message(
        f"✅ Registered this thread to project `#{project_id}`."
    )

@bot.slash_command(name="status", description="Check which Project ID this thread is linked to.")
async def status(interaction: Interaction):
    thread = interaction.channel

    if not isinstance(thread, Thread):
        await interaction.response.send_message("❌ This command can only be used inside a thread.", ephemeral=True)
        return

    db = load_db()
    thread_id = str(thread.id)

    if thread_id in db:
        entry = db[thread_id]
        await interaction.response.send_message(
            f"✅ This thread is linked to Project `#{entry['project_id']}`\n"
            f"🔗 Registered by: `{entry['registered_by']}`\n"
            f"🕓 Registered at: `{entry['timestamp']}`"
        )
    else:
        await interaction.response.send_message("❌ This thread is not registered to any project.")

@bot.slash_command(name="unregister", description="Unlink this thread from any Project ID.")
async def unregister(interaction: Interaction):
    thread = interaction.channel

    if not isinstance(thread, Thread):
        await interaction.response.send_message(
            "❌ This command can only be used inside a thread.", ephemeral=True
        )
        return

    # Permission check
    has_qc_role = next((r.id == QC_ROLE_ID for r in interaction.user.roles), False)
    has_manage_perm = interaction.user.guild_permissions.manage_messages

    if not has_qc_role and not has_manage_perm:
        await interaction.response.send_message(
            "🚫 You don't have permission to use this command.", ephemeral=True
        )
        return

    thread_id = str(thread.id)
    db = load_db()

    if thread_id not in db:
        await interaction.response.send_message(
            "⚠️ This thread is not registered to any project.", ephemeral=True
        )
        return

    del db[thread_id]
    save_db(db)

    await interaction.response.send_message("✅ Unregistered this thread from its project.")

@bot.slash_command(name="mark", description="Mark this thread's QC result.")
async def mark(
    interaction: Interaction,
    result: str = SlashOption(
        description="QC result",
        choices={"pass": "PASS", "fail": "FAIL"}
    ),
    reason: str = SlashOption(
        description="Reason (required for FAIL)",
        required=False
    )
):
    thread = interaction.channel

    if not isinstance(thread, Thread):
        await interaction.response.send_message("❌ This must be used in a thread.", ephemeral=True)
        return

    # Permission check
    has_qc_role = next((r.id == QC_ROLE_ID for r in interaction.user.roles), False)
    has_manage_perm = interaction.user.guild_permissions.manage_messages

    if not has_qc_role and not has_manage_perm:
        await interaction.response.send_message("🚫 You don't have permission to mark QC results.", ephemeral=True)
        return

    # Check registration
    db = load_db()
    thread_id = str(thread.id)
    if thread_id not in db:
        await interaction.response.send_message("❌ This thread is not registered to any project ID.", ephemeral=True)
        return

    project_id = db[thread_id]["project_id"]

    # Require reason if failed
    if result.lower() == "fail" and not reason:
        await interaction.response.send_message("⚠️ Please provide a reason when marking as FAIL.", ephemeral=True)
        return

    # Mark result
    success = sheets.markQCResult(project_id, result.upper(), reason)

    if success:
        await interaction.response.send_message(f"✅ Marked project `#{project_id}` as **{result.upper()}**.")

        try:
            await thread.edit(
                archived=True,
                locked=True,
                applied_tags=[]  # Clear tags first
            )
            pass_tag_id = int(os.getenv("PASS_TAG_ID", 1333406922098868326))
            fail_tag_id = int(os.getenv("FAIL_TAG_ID", 1333406950955810899))
            tag_id = pass_tag_id if result.lower() == "pass" else fail_tag_id
            await thread.edit(applied_tags=[nextcord.ForumTag(id=tag_id)])
        except Exception as e:
            print(f"[WARN] Failed to close or tag thread: {e}")

        # Unregister thread
        del db[thread_id]
        save_db(db)
    else:
        await interaction.response.send_message("❌ Could not update sheet. Check if the project exists or if fail reason is missing.", ephemeral=True)

@bot.slash_command(name="qc", description="Runs text quality control on a Canva URL.")
async def qc(interaction: Interaction, url: str):
    """Manually runs QC on a Canva URL."""
    await interaction.response.defer()

    # Check if the URL ends with `/edit`, change it to `/view`
    if url.endswith("/edit"):
        url = url.replace("/edit", "/view")
        print(f"Modified URL to: {url}")
    
    print(f"Found Canva URL: {url}")

    extracted_data = extract_text_and_fonts(url)
    final_data = map_fonts(extracted_data["text_data"], extracted_data["fonts"])
    categorized_text = categorize_text(final_data)

    total_score = 0
    total_possible_score = 0
    report = "## **Quality Control Report**\n"

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

    await interaction.followup.send(report)

@bot.slash_command(name="palette", description="Gets the palette for the given image.")
async def palette(interaction: nextcord.Interaction, file: nextcord.Attachment):
    await interaction.response.defer()

    try:
        # Download the image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Convert image to RGB mode and resize for efficiency
        image = image.convert("RGB")
        image = image.resize((150, 150))  # Slightly larger for better color sampling

        # Prepare the image data for k-means clustering
        pixels = np.float32(image).reshape(-1, 3)

        # Use k-means clustering to find dominant colors
        num_colors = 8
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
        flags = cv2.KMEANS_RANDOM_CENTERS
        _, labels, palette = cv2.kmeans(pixels, num_colors, None, criteria, 10, flags)

        # Calculate color frequencies
        _, counts = np.unique(labels, return_counts=True)
        
        # Sort colors by frequency
        colors_sorted = [(color, count) for color, count in zip(palette, counts)]
        colors_sorted.sort(key=lambda x: x[1], reverse=True)
        
        # Extract just the colors
        top_colors = [tuple(map(int, color)) for color, _ in colors_sorted]

        # Generate a preview image of the palette
        palette_width = 800
        palette_height = 100
        palette_img = Image.new("RGB", (palette_width, palette_height))
        draw = ImageDraw.Draw(palette_img)
        
        # Add color blocks and hex codes
        block_width = palette_width // len(top_colors)
        font = ImageFont.load_default(size=18)
        
        for i, color in enumerate(top_colors):
            # Draw color block
            x0 = i * block_width
            x1 = x0 + block_width
            draw.rectangle([x0, 0, x1, palette_height], fill=color)
            
            # Add hex code
            hex_code = '#{:02x}{:02x}{:02x}'.format(*color)
            # Calculate text position (centered in block)
            text_bbox = draw.textbbox((0, 0), hex_code, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = x0 + (block_width - text_width) // 2
            text_y = (palette_height - text_height) // 2
            draw.text((text_x, text_y), hex_code, fill='white' if sum(color) < 384 else 'black', font=font)

        # Convert preview image to bytes
        img_bytes = io.BytesIO()
        palette_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        # Send the palette
        file = nextcord.File(img_bytes, "palette.png")
        await interaction.followup.send("Here is the color palette:", file=file)
        
    except Exception as e:
        await interaction.followup.send(f"Error processing image: {str(e)}")

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
