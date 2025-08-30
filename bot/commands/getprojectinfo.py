"""
Get Project Info command - Gets info about a projectID.
"""

from typing import Any
from nextcord import Interaction, SlashOption, Embed
from backend import get_project_info


def setup(bot: Any, utils: Any) -> None:
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="getprojectinfo", description="Gets info about a projectID")
    async def getProjectInfo(
        interaction: Interaction,
        project_id: str = SlashOption(description="Project ID like #000003")
    ) -> None:
        # Clean the project ID
        clean_id: str = utils.clean_project_id(project_id)

        # Get project info using the backend API
        project_info = get_project_info(clean_id)
        if not project_info:
            await interaction.response.send_message(
                f"❌ Project ID `{clean_id}` not found.",
                ephemeral=True
            )
            return

        # Create embed with project information
        embed: Embed = Embed(
            title=f"📄 Project Info: {project_info['project_id']}",
            description=project_info.get('description', 'No description available'),
            color=0xB700FF
        )
        
        embed.add_field(name="📌 Project Name", value=project_info.get('name', 'N/A'), inline=False)
        embed.add_field(name="🔥 Priority", value=project_info.get('priority', 'N/A'), inline=True)
        embed.add_field(name="✍️ Writer", value=project_info.get('assigned_writer', 'Not assigned'), inline=True)
        embed.add_field(name="🎨 Designer", value=project_info.get('assigned_designer', 'Not assigned'), inline=True)
        embed.add_field(name="📋 Row", value=str(project_info.get('row', 'N/A')), inline=True)
        embed.set_footer(text="SteamXQuality Management System")

        await interaction.response.send_message(embed=embed)
