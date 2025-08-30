"""
Backend module for SteamXQuality project management.
Handles Google Sheets integration, data models, and assignment logic.
"""

from .sheets_api import *
from .models import *
from .assignment import *

__version__ = "1.0.0"
__all__ = [
    # Main API functions
    'format_project_id', 'get_project_row', 'get_project_info',
    'get_best_designers', 'get_best_writers', 'get_best_controllers',
    'assign_designer_to_project', 'assign_writer_to_project',
    'assign_writer_controller_to_project', 'assign_design_controller_to_project',
    'assign_all_to_project',  # The assign all function
    'auto_assign_unconnected_projects',  # The new auto-assign function for bot automation
    'get_assignment_recommendations', 'get_controller_recommendations',
    'bulk_assign_writers', 'bulk_assign_designers',
    'get_steam_topics',
    
    # Data models
    'PROJECT_COLUMNS', 'DESIGNER_COLUMNS', 'WRITER_COLUMNS', 'CONTROLLER_COLUMNS',
    'STEAMTopic', 'Designer', 'Writer', 'Controller',
    
    # Sheet objects (for advanced usage)
    'frontend_project', 'designer_sheet', 'writer_sheet', 'controller_sheet', 'contact_sheet'
]
