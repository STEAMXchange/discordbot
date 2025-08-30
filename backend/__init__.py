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
    'get_best_designers', 'get_best_writers',
    'assign_designer_to_project', 'assign_writer_to_project',
    'get_assignment_recommendations',
    'bulk_assign_writers', 'bulk_assign_designers',
    'get_steam_topics',
    
    # Data models
    'PROJECT_COLUMNS', 'DESIGNER_COLUMNS', 'WRITER_COLUMNS',
    'STEAMTopic', 'Designer', 'Writer',
    
    # Sheet objects (for advanced usage)
    'frontend_project', 'designer_sheet', 'writer_sheet', 'contact_sheet'
]
