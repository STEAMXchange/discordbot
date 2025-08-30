"""
Register command - Link a thread to a Project ID.
"""

from typing import Any
from nextcord import Interaction, Thread, SlashOption
from backend import get_project_row


def setup(bot: Any, utils: Any) -> None:
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="register", description="Link this thread to a Project ID.")
    async def register(interaction: Interaction, project_id: str = SlashOption(description="Project ID like #000003")) -> None:
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

        # Clean and validate project ID
        project_id = utils.clean_project_id(project_id)

        # Validate project ID exists
        if get_project_row(project_id) == -1:
            await interaction.response.send_message(
                f"❌ Project ID `#{project_id}` does not exist.", ephemeral=True
            )
            return

        # Register thread using utils
        thread_id: str = str(thread.id)
        utils.register_thread(thread_id, project_id, interaction.user.name)

        await interaction.response.send_message(
            f"✅ Registered this thread to project `#{project_id}`."
        )
