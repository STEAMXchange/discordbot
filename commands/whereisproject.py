"""
Where is Project command - Find the thread/location of a project ID.
"""

from nextcord import Interaction, SlashOption
import sheets


def setup(bot, utils):
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="whereisproject", description="Find the thread/location of a project ID")
    async def whereisproject(
        interaction: Interaction,
        project_id: str = SlashOption(description="Project ID like #000003")
    ):
        # Clean up the project ID
        clean_project_id = utils.clean_project_id(project_id)
        
        # Check if project exists first
        if not sheets.projectExists(clean_project_id):
            await interaction.response.send_message(f"❌ Project `#{clean_project_id}` does not exist.", ephemeral=True)
            return
        
        # Find thread using utils
        found_thread_id = utils.find_project_thread(clean_project_id)
        
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
