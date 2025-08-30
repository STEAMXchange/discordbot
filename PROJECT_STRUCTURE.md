# SteamXQuality Project Structure

## 📁 New Organized Structure

```
steamxquality/
├── 🤖 bot/                          # Discord Bot Module
│   ├── __init__.py                  # Bot module initialization
│   ├── qc_main.py                   # Main bot file
│   ├── utils.py                     # Bot utilities and helpers
│   ├── qc_helpers.py                # Quality control helper functions
│   └── commands/                    # Bot slash commands
│       ├── __init__.py
│       ├── about.py                 # Bot info command
│       ├── getprojectid.py          # Get project ID from thread
│       ├── getprojectinfo.py        # Get project information
│       ├── geturl.py                # Get Canva URL
│       ├── kill.py                  # Shutdown bot (admin only)
│       ├── mark.py                  # Mark QC results
│       └── register.py              # Register thread to project
│
├── 🔧 backend/                      # Backend/Sheets Module
│   ├── __init__.py                  # Backend module exports
│   ├── models.py                    # Data models and enums
│   ├── helpers.py                   # Utility functions
│   ├── assignment.py                # Assignment logic
│   └── sheets_api.py                # Clean Google Sheets API
│
├── 📄 Configuration & Entry Points
│   ├── main.py                      # Main entry point
│   ├── requirements.txt             # Python dependencies
│   ├── env.example                  # Environment variables template
│   └── .env                         # Environment variables (not in git)
│
├── 📚 Documentation
│   ├── README.md                    # Main documentation
│   ├── PROJECT_STRUCTURE.md         # This file
│   ├── MIGRATION_GUIDE.md           # Migration from old structure
│   └── DEPLOYMENT.md                # Deployment instructions
│
└── 🗃️ Legacy/Backup Files
    ├── sheets.py                    # Original monolithic file
    ├── sheets_clean.py              # Intermediate clean version
    ├── qc.py                        # Original bot file
    └── commands/                    # Original commands folder
```

## 🎯 Key Benefits

### **Separation of Concerns**
- **Bot Module**: Handles Discord interactions, commands, and bot-specific logic
- **Backend Module**: Manages Google Sheets integration, data models, and assignment logic
- **Clear Boundaries**: Each module has a specific responsibility

### **Improved Maintainability**
- **Smaller Files**: Easier to understand and modify
- **Focused Modules**: Each file has a single, clear purpose
- **Better Organization**: Related functionality is grouped together

### **Enhanced Testability**
- **Modular Design**: Each module can be tested independently
- **Mock-Friendly**: Easy to mock dependencies for unit tests
- **Isolated Logic**: Business logic separated from Discord API calls

### **Type Safety**
- **Comprehensive Typing**: All modules have proper type annotations
- **Clear Interfaces**: Well-defined function signatures and return types
- **Better IDE Support**: Enhanced autocomplete and error detection

## 🚀 Usage Examples

### Running the Bot
```bash
# Run the Discord bot
python main.py bot

# Or directly
python -m bot.qc_main
```

### Using the Backend API
```bash
# Run backend demo
python main.py backend

# Or use in Python code
from backend import get_project_info, assign_writer_to_project

project = get_project_info("000001")
assign_writer_to_project("000001", "Science")
```

### Importing Specific Components
```python
# Import data models
from backend.models import STEAMTopic, Designer, Writer

# Import utilities
from backend.helpers import formatPID, getProjectRow

# Import assignment logic
from backend.assignment import getBestWriter, assignDesigner

# Import bot utilities
from bot.utils import BotUtils
```

## 🔄 Migration Path

### For Existing Code
1. **Update Imports**: Change `import sheets` to `from backend import *`
2. **Use New API**: Replace function calls with new clean API functions
3. **Update Bot**: Use new modular bot structure

### For New Development
1. **Use Backend Module**: For all Google Sheets operations
2. **Use Bot Module**: For all Discord-related functionality
3. **Follow Structure**: Keep related code in appropriate modules

## 📦 Module Details

### Backend Module (`backend/`)
- **`models.py`**: STEAMTopic enum, Designer/Writer dataclasses, column mappings
- **`helpers.py`**: formatPID, getProjectRow, penalty calculations, row processing
- **`assignment.py`**: getBestDesigner, getBestWriter, assignment functions
- **`sheets_api.py`**: High-level API functions, Google Sheets connection

### Bot Module (`bot/`)
- **`qc_main.py`**: Main bot file, event handlers, QC automation
- **`utils.py`**: Bot utilities, thread management, permissions
- **`qc_helpers.py`**: Quality control specific functions, Canva processing
- **`commands/`**: Individual slash command implementations

## 🔧 Configuration

### Environment Variables
```env
# Discord Bot
DISCORD_BOT_TOKEN=your_bot_token
FORUM_CHANNEL_ID=1333405556714504242
QC_ROLE_ID=1333429556429721674

# Google Sheets
PROJECT_SHEET_ID=your_project_sheet_id
MANAGEMENT_SHEET_ID=your_management_sheet_id
GOOGLE_CREDENTIALS_FILE=steamxquality-credentials.json
```

### Dependencies
- **Discord**: `nextcord`, `python-dotenv`
- **Google Sheets**: `gspread`, `oauth2client`
- **Quality Control**: `selenium`, `webdriver-manager`, `pillow`
- **Type Safety**: Full type annotations throughout

This new structure provides a solid foundation for future development while maintaining backward compatibility and improving code quality significantly.
