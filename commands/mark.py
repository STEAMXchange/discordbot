"""
Mark command - Mark this thread's QC result.
"""

import os
from nextcord import Interaction, Thread, SlashOption, ForumTag
import sheets
from utils import PASS_TAG_ID, FAIL_TAG_ID


def setup(bot, utils):
    """Setup function to register the command with the bot."""
    
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

        # Check permissions using utils
        if not utils.has_qc_permission(interaction.user):
            await interaction.response.send_message("🚫 You don't have permission to mark QC results.", ephemeral=True)
            return

        # Check registration
        thread_id = str(thread.id)
        project_info = utils.get_thread_project(thread_id)
        
        if not project_info:
            await interaction.response.send_message("❌ This thread is not registered to any project ID.", ephemeral=True)
            return

        project_id = project_info["project_id"]

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
                tag_id = PASS_TAG_ID if result.lower() == "pass" else FAIL_TAG_ID
                await thread.edit(applied_tags=[ForumTag(id=tag_id)])
            except Exception as e:
                print(f"[WARN] Failed to close or tag thread: {e}")

            # Unregister thread using utils
            utils.unregister_thread(thread_id)
        else:
            await interaction.response.send_message("❌ Could not update sheet. Check if the project exists or if fail reason is missing.", ephemeral=True)
