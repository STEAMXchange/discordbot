"""
Unregister command - Unlink a thread from any Project ID.
"""

from nextcord import Interaction, Thread


def setup(bot, utils):
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="unregister", description="Unlink this thread from any Project ID.")
    async def unregister(interaction: Interaction):
        thread = interaction.channel

        if not isinstance(thread, Thread):
            await interaction.response.send_message(
                "❌ This command can only be used inside a thread.", ephemeral=True
            )
            return

        # Check permissions using utils
        if not utils.has_qc_permission(interaction.user):
            await interaction.response.send_message(
                "🚫 You don't have permission to use this command.", ephemeral=True
            )
            return

        thread_id = str(thread.id)
        
        # Try to unregister using utils
        if not utils.unregister_thread(thread_id):
            await interaction.response.send_message(
                "⚠️ This thread is not registered to any project.", ephemeral=True
            )
            return

        await interaction.response.send_message("✅ Unregistered this thread from its project.")
