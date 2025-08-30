"""
Utility functions and shared objects for the Quality Control bot.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Database file path
DB_FILE = "thread_db.json"

# Role and channel IDs
QC_ROLE_ID = int(os.getenv("QC_ROLE_ID", 1333429556429721674))
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID", 1333405556714504242))

# Tag IDs
PASS_TAG_ID = int(os.getenv("PASS_TAG_ID", 1333406922098868326))
FAIL_TAG_ID = int(os.getenv("FAIL_TAG_ID", 1333406950955810899))
STALLED_TAG_ID = int(os.getenv("STALLED_TAG_ID", 1355469672278917264))


class BotUtils:
    """Utility class containing shared bot functionality."""
    
    def __init__(self, bot: Any) -> None:
        self.bot = bot
    
    def load_db(self) -> Dict[str, Any]:
        """Load the thread database from JSON file."""
        if not os.path.exists(DB_FILE):
            return {}
        with open(DB_FILE, "r") as f:
            return json.load(f)
    
    def save_db(self, data: Dict[str, Any]) -> None:
        """Save the thread database to JSON file."""
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)
    
    def has_qc_permission(self, user: Any) -> bool:
        """Check if user has QC role or manage messages permission."""
        has_qc_role: bool = next((r.id == QC_ROLE_ID for r in user.roles), False)
        has_manage_perm: bool = user.guild_permissions.manage_messages
        return has_qc_role or has_manage_perm
    
    def register_thread(self, thread_id: str, project_id: str, registered_by: str) -> None:
        """Register a thread to a project ID."""
        db: Dict[str, Any] = self.load_db()
        db[thread_id] = {
            "project_id": project_id,
            "registered_by": registered_by,
            "timestamp": datetime.now().isoformat()
        }
        self.save_db(db)
    
    def unregister_thread(self, thread_id: str) -> bool:
        """Unregister a thread from its project ID. Returns True if thread was registered."""
        db: Dict[str, Any] = self.load_db()
        if thread_id in db:
            del db[thread_id]
            self.save_db(db)
            return True
        return False
    
    def get_thread_project(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get project info for a thread. Returns None if not registered."""
        db: Dict[str, Any] = self.load_db()
        return db.get(thread_id)
    
    def find_project_thread(self, project_id: str) -> Optional[str]:
        """Find thread ID for a given project ID."""
        db: Dict[str, Any] = self.load_db()
        for thread_id, info in db.items():
            if info["project_id"] == project_id:
                return thread_id
        return None
    
    def clean_project_id(self, project_id: str) -> str:
        """Clean and format project ID (remove # and pad with zeros)."""
        return project_id.lstrip("#").zfill(6)


# Global utils instance (will be set in main file)
utils: Optional[BotUtils] = None
