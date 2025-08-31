"""
Discord UI components for SteamXQuality bot.
Contains views, buttons, and interactive components.
"""

import logging
from datetime import datetime
import nextcord
from .user_lookup import get_discord_username_from_name, get_user_by_username

logger = logging.getLogger(__name__)


class AssignmentView(nextcord.ui.View):
    """View with accept/decline buttons for assignment DMs."""
    
    def __init__(self, project_id: str, person_name: str, role_type: str):
        super().__init__(timeout=86400)  # 24 hour timeout
        self.project_id = project_id
        self.person_name = person_name
        self.role_type = role_type
        
    @nextcord.ui.button(label="✅ Accept", style=nextcord.ButtonStyle.green, custom_id="accept_assignment")
    async def accept_assignment(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Handle assignment acceptance."""
        try:
            # Update the original message to show acceptance
            embed = nextcord.Embed(
                title="✅ Assignment Accepted!",
                description=f"You have accepted the {self.role_type} role for project #{self.project_id}",
                color=nextcord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="📋 Status", value="Assignment confirmed", inline=False)
            embed.add_field(name="🚀 Next Steps", value="Check the project sheet for details and get started!", inline=False)
            embed.set_footer(text="SteamXQuality Assignment System")
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
                
            await interaction.response.edit_message(embed=embed, view=self)
            logger.info(f"✅ {self.person_name} accepted assignment for project #{self.project_id} as {self.role_type}")
            
        except Exception as e:
            logger.error(f"❌ Error handling assignment acceptance: {e}")
            await interaction.response.send_message("❌ Error processing acceptance. Please contact support.", ephemeral=True)
    
    @nextcord.ui.button(label="❌ Decline", style=nextcord.ButtonStyle.red, custom_id="decline_assignment")
    async def decline_assignment(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Handle assignment decline - will trigger reassignment."""
        try:
            # Update the original message to show decline
            embed = nextcord.Embed(
                title="❌ Assignment Declined",
                description=f"You have declined the {self.role_type} role for project #{self.project_id}",
                color=nextcord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="📋 Status", value="Assignment declined - automatic reassignment initiated", inline=False)
            embed.add_field(name="🔄 Next Steps", value="The system will find another available team member.", inline=False)
            embed.set_footer(text="SteamXQuality Assignment System")
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
                
            await interaction.response.edit_message(embed=embed, view=self)
            logger.info(f"❌ {self.person_name} declined assignment for project #{self.project_id} as {self.role_type}")
            
            # Trigger reassignment
            await self.handle_reassignment()
            
        except Exception as e:
            logger.error(f"❌ Error handling assignment decline: {e}")
            await interaction.response.send_message("❌ Error processing decline. Please contact support.", ephemeral=True)
    
    async def handle_reassignment(self):
        """Handle automatic reassignment when someone declines."""
        try:
            logger.info(f"🔄 Starting reassignment for project #{self.project_id} ({self.role_type})")
            
            # Import backend functions
            from backend import (
                frontend_project, designer_sheet, writer_sheet, controller_sheet,
                assignDesigner, assignWriter, assignWriterController, assignDesignerController
            )
            
            # Clear the previous assignment in the sheet
            await self.clear_assignment()
            
            # Perform reassignment based on role type
            if self.role_type == "designer":
                assignDesigner(self.project_id, frontend_project, designer_sheet)
                assignDesignerController(self.project_id, frontend_project, controller_sheet)
                logger.info(f"🔄 Reassigned designer and design controller for project #{self.project_id}")
            elif self.role_type == "writer":
                assignWriter(self.project_id, frontend_project, writer_sheet)
                assignWriterController(self.project_id, frontend_project, controller_sheet)
                logger.info(f"🔄 Reassigned writer and writer controller for project #{self.project_id}")
            elif self.role_type == "writer_controller":
                assignWriterController(self.project_id, frontend_project, controller_sheet)
                logger.info(f"🔄 Reassigned writer controller for project #{self.project_id}")
            elif self.role_type == "design_controller":
                assignDesignerController(self.project_id, frontend_project, controller_sheet)
                logger.info(f"🔄 Reassigned design controller for project #{self.project_id}")
            
            # Get newly assigned person and send them a DM
            await self.notify_new_assignee()
            
        except Exception as e:
            logger.error(f"❌ Error during reassignment: {e}")
    
    async def clear_assignment(self):
        """Clear the declined person from the project sheet."""
        try:
            from backend import frontend_project, getProjectRow, column_to_number, PROJECT_COLUMNS
            
            row = getProjectRow(self.project_id, frontend_project)
            if row == -1:
                return
                
            # Clear the appropriate column based on role type
            if self.role_type == "designer":
                col = column_to_number(PROJECT_COLUMNS.ASSIGNED_DESIGNER)
            elif self.role_type == "writer":
                col = column_to_number(PROJECT_COLUMNS.ASSIGNED_WRITER)
            elif self.role_type == "writer_controller":
                col = column_to_number(PROJECT_COLUMNS.WRITER_QC_CONTROLLER)
            elif self.role_type == "design_controller":
                col = column_to_number(PROJECT_COLUMNS.DESIGN_QC_CONTROLLER)
            else:
                return
                
            # Clear the cell
            frontend_project.update_cell(row, col, "")
            logger.info(f"🧹 Cleared {self.role_type} assignment for project #{self.project_id}")
            
        except Exception as e:
            logger.error(f"❌ Error clearing assignment: {e}")
    
    async def notify_new_assignee(self):
        """Send DM to the newly assigned person."""
        try:
            from backend import frontend_project, getProjectRow, column_to_number, PROJECT_COLUMNS
            from .notifications import send_individual_dm
            
            row = getProjectRow(self.project_id, frontend_project)
            if row == -1:
                return
                
            # Get the new assignee name based on role type
            if self.role_type == "designer":
                col = column_to_number(PROJECT_COLUMNS.ASSIGNED_DESIGNER)
            elif self.role_type == "writer":
                col = column_to_number(PROJECT_COLUMNS.ASSIGNED_WRITER)
            elif self.role_type == "writer_controller":
                col = column_to_number(PROJECT_COLUMNS.WRITER_QC_CONTROLLER)
            elif self.role_type == "design_controller":
                col = column_to_number(PROJECT_COLUMNS.DESIGN_QC_CONTROLLER)
            else:
                return
                
            new_assignee = frontend_project.cell(row, col).value
            if new_assignee and new_assignee.strip():
                await send_individual_dm(self.role_type, new_assignee.strip(), self.project_id)
                logger.info(f"🔄 Notified new assignee {new_assignee} for project #{self.project_id}")
            
        except Exception as e:
            logger.error(f"❌ Error notifying new assignee: {e}")
    
    async def on_timeout(self):
        """Handle view timeout - disable buttons."""
        for item in self.children:
            item.disabled = True
