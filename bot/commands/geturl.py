"""
Get URL command - Get the Canva URL for this thread's project.
"""

from typing import Any, Optional, Dict
from nextcord import Interaction, Thread


def setup(bot: Any, utils: Any) -> None:
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="geturl", description="Get the Canva URL for this thread's project.")
    async def canva(interaction: Interaction) -> None:
        thread = interaction.channel

        if not isinstance(thread, Thread):
            await interaction.response.send_message("❌ This command can only be used inside a thread.", ephemeral=True)
            return

        thread_id: str = str(thread.id)
        project_info: Optional[Dict[str, Any]] = utils.get_thread_project(thread_id)

        if not project_info:
            await interaction.response.send_message("❌ This thread is not registered to any project.", ephemeral=True)
            return

        project_id: str = project_info['project_id']
        
        # TODO: Implement getCanvaURL function in backend
        await interaction.response.send_message(f"🎨 Project `#{project_id}` - Canva URL functionality not yet implemented.")
