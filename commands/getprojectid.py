"""
Get Project ID command - Get the project ID linked to this thread.
"""

from nextcord import Interaction, Thread


def setup(bot, utils):
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="getprojectid", description="Get the project ID linked to this thread")
    async def getprojectid(interaction: Interaction):
        thread = interaction.channel
        
        if not isinstance(thread, Thread):
            await interaction.response.send_message("❌ This command can only be used inside a thread.", ephemeral=True)
            return
        
        thread_id = str(thread.id)
        project_info = utils.get_thread_project(thread_id)
        
        if project_info:
            project_id = project_info["project_id"]
            await interaction.response.send_message(f"📋 Project ID: `#{project_id}`", ephemeral=True)
        else:
            await interaction.response.send_message("❌ This thread is not registered to any project.", ephemeral=True)
