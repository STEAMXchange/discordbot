"""
Get URL command - Get the Canva URL for this thread's project.
"""

from nextcord import Interaction, Thread
from sheets import getCanvaURL


def setup(bot, utils):
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="geturl", description="Get the Canva URL for this thread's project.")
    async def canva(interaction: Interaction):
        thread = interaction.channel

        if not isinstance(thread, Thread):
            await interaction.response.send_message("❌ This command can only be used inside a thread.", ephemeral=True)
            return

        thread_id = str(thread.id)
        project_info = utils.get_thread_project(thread_id)

        if not project_info:
            await interaction.response.send_message("❌ This thread is not registered to any project.", ephemeral=True)
            return

        project_id = project_info['project_id']
        canva_url = getCanvaURL(project_id)

        if canva_url and canva_url != "IMAGE SENT IN QC CHAT":
            await interaction.response.send_message(f"🎨 Canva URL for Project `#{project_id}`: {canva_url}")
        elif canva_url == "IMAGE SENT IN QC CHAT":
            await interaction.response.send_message(f"📸 Project `#{project_id}`: Design was sent directly in QC chat (no Canva link)")
        else:
            await interaction.response.send_message(f"❌ No Canva URL found for Project `#{project_id}`")
