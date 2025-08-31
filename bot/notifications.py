"""
Notification and DM handling for SteamXQuality bot.
Contains all logic for sending DMs about assignments and QC results.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import nextcord
from .user_lookup import get_discord_username_from_name, get_user_by_username
from .views import AssignmentView

logger = logging.getLogger(__name__)


async def send_assignment_dms(results: Dict[str, Any]):
    """Send DMs to all people who were assigned to projects."""
    try:
        assignments = results.get('assignments', {})
        if not assignments:
            logger.info("📧 No assignments to send DMs for")
            return
            
        dm_count = 0
        
        for project_id, assignment_result in assignments.items():
            if 'error' in assignment_result:
                continue
                
            # Send DM for each assigned role
            for role, status in assignment_result.items():
                if status == "Assigned":
                    await send_assignment_dm_for_role(project_id, role)
                    dm_count += 1
        
        logger.info(f"📧 Sent {dm_count} assignment DMs")
        
    except Exception as e:
        logger.error(f"❌ Failed to send assignment DMs: {e}")


async def send_assignment_dm_for_role(project_id: str, role: str):
    """Send assignment DM for a specific role on a project."""
    try:
        from backend import frontend_project, getProjectRow, column_to_number, PROJECT_COLUMNS
        
        row = getProjectRow(project_id, frontend_project)
        if row == -1:
            return
            
        # Get the assigned person's name based on role
        if role == "writer":
            col = column_to_number(PROJECT_COLUMNS.ASSIGNED_WRITER)
        elif role == "designer":
            col = column_to_number(PROJECT_COLUMNS.ASSIGNED_DESIGNER)
        elif role == "writer_controller":
            col = column_to_number(PROJECT_COLUMNS.WRITER_QC_CONTROLLER)
        elif role == "design_controller":
            col = column_to_number(PROJECT_COLUMNS.DESIGN_QC_CONTROLLER)
        else:
            return
            
        person_name = frontend_project.cell(row, col).value
        if person_name and person_name.strip():
            await send_individual_dm(role, person_name.strip(), project_id)
        
    except Exception as e:
        logger.error(f"❌ Failed to send assignment DM for {role} on project #{project_id}: {e}")


async def send_designer_assignment_dms(results: Dict[str, Any]):
    """Send DMs to designers who were assigned to projects."""
    try:
        assignments = results.get('assignments', {})
        if not assignments:
            return
            
        # Get all assigned designers from the results
        assigned_designers = set()
        for project_id, assignment_result in assignments.items():
            if 'error' not in assignment_result and assignment_result.get('designer') == 'Assigned':
                # Get the actual assigned designer name
                from backend import get_project_info
                
                try:
                    project_info = get_project_info(project_id)
                    if project_info and 'assigned_designer' in project_info:
                        designer_name = project_info['assigned_designer']
                        if designer_name and designer_name.strip():
                            assigned_designers.add((designer_name.strip(), project_id))
                except Exception as e:
                    logger.error(f"❌ Failed to get designer info for project {project_id}: {e}")
                    continue
        
        # Send DMs to all assigned designers
        for designer_name, project_id in assigned_designers:
            await send_individual_dm("designer", designer_name, project_id)
            
        logger.info(f"📧 Sent designer assignment DMs to {len(assigned_designers)} designers")
        
    except Exception as e:
        logger.error(f"❌ Failed to send designer assignment DMs: {e}")


async def send_individual_dm(role_type: str, person_name: str, project_id: str):
    """Send a DM to an individual person about their assignment."""
    try:
        # Step 1: Name → Discord Username (from sheets)
        discord_username = await get_discord_username_from_name(person_name, role_type)
        if not discord_username:
            logger.warning(f"⚠️  No Discord username found for {person_name} ({role_type})")
            return
            
        # Step 2: Discord Username → User ID (from server members)
        user = await get_user_by_username(discord_username)
        if not user:
            logger.warning(f"⚠️  Discord user not found: {discord_username}")
            return
            
        # Step 3: Send DM with context-aware messaging
        try:
            # Determine if this is a phase-aware assignment (designer after writing completion)
            is_phase_assignment = role_type == "designer"
            
            embed = nextcord.Embed(
                title="🎯 New Project Assignment!" if not is_phase_assignment else "🎨 Design Phase Ready!",
                description=(
                    f"You've been assigned to project #{project_id}" if not is_phase_assignment
                    else f"Writing is complete! You can now start design work on project #{project_id}"
                ),
                color=nextcord.Color.blue() if not is_phase_assignment else nextcord.Color.purple(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 Your Role",
                value=role_type.title(),
                inline=True
            )
            
            embed.add_field(
                name="🆔 Project ID", 
                value=f"#{project_id}",
                inline=True
            )
            
            if is_phase_assignment:
                embed.add_field(
                    name="✅ Writing Status",
                    value="Complete - QC approved",
                    inline=True
                )
            
            embed.add_field(
                name="📊 Next Steps",
                value=(
                    "Check the project sheet for details and deadlines!" if not is_phase_assignment
                    else "Writing QC is complete. Check the project sheet for design requirements and deadlines!"
                ),
                inline=False
            )
            
            embed.set_footer(text="SteamXQuality Phase-Aware Assignment System")
            
            # Create accept/decline buttons
            view = AssignmentView(project_id, person_name, role_type)
            
            await user.send(embed=embed, view=view)
            logger.info(f"📧 DM with accept/decline buttons sent to {person_name} ({discord_username}) for project #{project_id}")
            
        except nextcord.Forbidden:
            logger.warning(f"⚠️  Cannot DM {discord_username} (DMs disabled)")
        except Exception as dm_error:
            logger.error(f"❌ Failed to DM {discord_username}: {dm_error}")
            
    except Exception as e:
        logger.error(f"❌ Failed to send individual DM to {person_name}: {e}")


async def send_qc_result_notifications(qc_notifications: List[Dict]):
    """Send DMs to notify about QC results."""
    try:
        for qc_result in qc_notifications:
            project_id = qc_result['project_id']
            qc_type = qc_result['type']  # 'writer' or 'designer'
            result = qc_result['result']  # 'PASS' or 'FAIL'
            assignee = qc_result['assignee']
            qc_controller = qc_result['qc_controller']
            
            if assignee:
                await send_qc_result_dm(assignee, project_id, qc_type, result, qc_controller)
            
            # Also notify the QC controller
            if qc_controller:
                await send_qc_controller_dm(qc_controller, project_id, qc_type, result, assignee)
                
    except Exception as e:
        logger.error(f"❌ Error sending QC result notifications: {e}")


async def send_qc_result_dm(assignee_name: str, project_id: str, qc_type: str, result: str, qc_controller: str):
    """Send DM to assignee about their QC result."""
    try:
        # Get Discord user
        discord_username = await get_discord_username_from_name(assignee_name, qc_type)
        if not discord_username:
            return
            
        user = await get_user_by_username(discord_username)
        if not user:
            return
            
        # Create embed based on result
        if result == "PASS":
            embed = nextcord.Embed(
                title="✅ QC Passed!",
                description=f"Great news! Your {qc_type} work on project #{project_id} has passed QC review.",
                color=nextcord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Status", value="APPROVED ✅", inline=True)
            if qc_type == "writer":
                embed.add_field(name="🎨 Next Phase", value="Design work can now begin", inline=True)
        else:  # FAIL
            embed = nextcord.Embed(
                title="🔄 QC Revision Required",
                description=f"Your {qc_type} work on project #{project_id} needs revision based on QC feedback.",
                color=nextcord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Status", value="NEEDS REVISION 🔄", inline=True)
            embed.add_field(name="🔧 Next Steps", value="Check QC feedback and submit revisions", inline=True)
        
        embed.add_field(name="🆔 Project", value=f"#{project_id}", inline=True)
        embed.add_field(name="🔍 QC Controller", value=qc_controller, inline=True)
        embed.set_footer(text="SteamXQuality QC System")
        
        await user.send(embed=embed)
        logger.info(f"📧 QC result DM sent to {assignee_name}: Project #{project_id} {qc_type} QC {result}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send QC result DM to {assignee_name}: {e}")


async def send_qc_controller_dm(controller_name: str, project_id: str, qc_type: str, result: str, assignee: str):
    """Send DM to QC controller confirming their review was processed."""
    try:
        # Get Discord user
        discord_username = await get_discord_username_from_name(controller_name, f"{qc_type}_controller")
        if not discord_username:
            return
            
        user = await get_user_by_username(discord_username)
        if not user:
            return
            
        embed = nextcord.Embed(
            title="📋 QC Review Processed",
            description=f"Your QC review for project #{project_id} has been processed and the {qc_type} has been notified.",
            color=nextcord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="🆔 Project", value=f"#{project_id}", inline=True)
        embed.add_field(name=f"👤 {qc_type.title()}", value=assignee, inline=True)
        embed.add_field(name="📊 Your Decision", value=f"{result} {'✅' if result == 'PASS' else '🔄'}", inline=True)
        
        if result == "PASS" and qc_type == "writer":
            embed.add_field(name="🎨 Impact", value="Design phase can now begin", inline=False)
        
        embed.set_footer(text="SteamXQuality QC System")
        
        await user.send(embed=embed)
        logger.info(f"📧 QC confirmation DM sent to controller {controller_name}: Project #{project_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send QC confirmation DM to {controller_name}: {e}")


async def send_assignment_notification(results: Dict[str, Any]):
    """Send DMs to people who were assigned to projects."""
    try:
        logger.info("🤖 Processing assignment notifications - DMs only")
        
        # Skip all channel-related code - DMs only
        await send_assignment_dms(results)
        
    except Exception as e:
        logger.error(f"❌ Failed to send assignment DMs: {e}")


async def send_designer_assignment_notification(results: Dict[str, Any]):
    """Send DMs to designers who were assigned to projects."""
    try:
        logger.info("🎨 Processing designer assignment notifications - DMs only")
        
        # Skip all channel-related code - DMs only
        await send_designer_assignment_dms(results)
        
    except Exception as e:
        logger.error(f"❌ Failed to send designer assignment DMs: {e}")
