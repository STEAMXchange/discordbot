"""
Get Project Info command - Gets info about a projectID.
"""

from nextcord import Interaction, SlashOption, Embed
import sheets


def setup(bot, utils):
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="getprojectinfo", description="Gets info about a projectID")
    async def getProjectInfo(
        interaction: Interaction,
        project_id: str = SlashOption(description="Project ID like #000003")
    ):
        # Clean the project ID
        clean_id = utils.clean_project_id(project_id)

        if not sheets.projectExists(clean_id):
            await interaction.response.send_message(content=f"Project id: {clean_id} not found!", ephemeral=True)
            return

        row = sheets.getProjectRow(clean_id)

        if not row:
            await interaction.response.send_message(
                f"❌ Project ID `{clean_id}` not found.",
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
