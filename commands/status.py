"""
Status command - Check which Project ID this thread is linked to.
"""

from nextcord import Interaction, Thread


def setup(bot, utils):
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="status", description="Check which Project ID this thread is linked to.")
    async def status(interaction: Interaction):
        thread = interaction.channel

        if not isinstance(thread, Thread):
            await interaction.response.send_message("❌ This command can only be used inside a thread.", ephemeral=True)
            return

        thread_id = str(thread.id)
        project_info = utils.get_thread_project(thread_id)

        if project_info:
            await interaction.response.send_message(
                f"✅ This thread is linked to Project `#{project_info['project_id']}`\n"
                f"🔗 Registered by: `{project_info['registered_by']}`\n"
                f"🕓 Registered at: `{project_info['timestamp']}`"
            )
        else:
            await interaction.response.send_message("❌ This thread is not registered to any project.")
