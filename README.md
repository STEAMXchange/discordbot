# 🤖 SteamXQuality - Automated Project Management System

A comprehensive Discord bot that automates project assignment and quality control processes, integrating with Google Sheets for seamless workflow management.

## ✨ Features

### 🔄 **Automated Project Assignment**
- **Smart Resource Assignment**: Automatically assigns writers, designers, and QC controllers based on skills and workload
- **Real-time Processing**: Scans for new projects every 5 minutes
- **Intelligent Matching**: Uses ranking algorithms for optimal assignments
- **Auto-marking**: Marks processed projects as "CONNECTED"

### 📊 **Google Sheets Integration**
- **Live Sync**: Real-time project data synchronization
- **Assignment Tracking**: Monitors workloads and completion rates
- **Statistics**: Comprehensive analytics and reporting
- **Multi-sheet Support**: Projects, Designers, Writers, Controllers sheets

### 🎛️ **Discord Bot Commands**
- **Timer Management**: `/timer_status` to monitor automation
- **Project Info**: Get detailed project information
- **Quality Control**: Automated QC assignment and tracking
- **Permission System**: Role-based access control

### 🚀 **Backend API**
- **Assignment Engine**: Intelligent resource allocation algorithms
- **Data Models**: Clean data structures for all entities
- **Helper Functions**: Utilities for sheet operations and formatting

## 🚀 Quick Start

### 1. **Installation**
```bash
git clone <repository>
cd steamxquality
pip install -r requirements.txt
```

### 2. **Configuration**
Create a `.env` file from `env.example`:
```env
DISCORD_BOT_TOKEN=your_discord_token
PROJECT_SHEET_ID=your_google_sheet_id
MANAGEMENT_SHEET_ID=your_management_sheet_id
GOOGLE_CREDENTIALS_FILE=your_credentials.json
QC_ROLE_ID=your_qc_role_id
OWNER_USER_ID=your_discord_user_id
```

### 3. **Google Sheets Setup**
- Create a Google Cloud Project
- Enable Google Sheets API
- Create service account credentials
- Share your sheets with the service account email

### 4. **Run the Bot**
```bash
# Recommended method
python run_bot.py

# Or directly
python bot/bot.py
```

## 📁 Project Structure

```
steamxquality/
├── 🤖 bot/                     # Discord Bot
│   ├── bot.py                  # Main bot file
│   ├── timers.py              # Automated tasks (@tasks.loop)
│   └── __init__.py            # Package init
├── 🔧 backend/                # Assignment Engine
│   ├── sheets_api.py          # Main API interface
│   ├── assignment.py          # Assignment algorithms
│   ├── models.py              # Data models
│   ├── helpers.py             # Utility functions
│   └── test.py                # Testing playground
├── 📋 Requirements & Config
│   ├── requirements.txt       # Python dependencies
│   ├── env.example           # Environment template
│   └── run_bot.py            # Bot launcher script
└── 📄 Documentation
    └── README.md             # This file
```

## 🎯 How It Works

### **Automated Assignment Flow:**
1. **🔍 Scanning**: Every 5 minutes, scans for unconnected projects
2. **✅ Validation**: Checks if project is `READY_TO_ASSIGN = "YES"`
3. **🧠 Assignment**: Uses smart algorithms to assign:
   - **Writer** (based on topic expertise and workload)
   - **Designer** (based on platform skills and priority)
   - **QC Controllers** (for both writing and design)
4. **🔗 Marking**: Sets `PROJECT_CONNECTED = "YES"`
5. **📢 Notification**: Sends Discord notification with results

### **Assignment Algorithms:**
- **Writers**: Ranked by topic match, KPI, and current workload
- **Designers**: Ranked by platform expertise, KPI, and priority
- **Controllers**: Ranked by speciality match and availability

## 🎛️ Discord Commands

### **Timer Management**
- `/timer_status` - View automation status and statistics
- Permission: QC role or bot owner

### **Backend API Functions**
Available in Python scripts:
```python
from backend import (
    assign_all_to_project,           # Assign everything needed
    auto_assign_unconnected_projects, # Scan and assign all
    get_assignment_recommendations,   # Get suggestions
    assign_writer_to_project,        # Assign specific roles
    assign_design_controller_to_project
)

# Example usage
results = assign_all_to_project("000001")
summary = auto_assign_unconnected_projects()
```

## 🔧 Development

### **Testing the Backend**
```bash
python backend/test.py
```

### **Adding New Features**
1. **Models**: Add data structures in `backend/models.py`
2. **Logic**: Implement algorithms in `backend/assignment.py`
3. **API**: Expose functions in `backend/sheets_api.py`
4. **Bot**: Add Discord commands in `bot/bot.py`

### **Timer Customization**
Edit intervals in `bot/timers.py`:
```python
@tasks.loop(minutes=5)   # Auto-assignment frequency
@tasks.loop(minutes=15)  # Spreadsheet updates
```

## 📊 Statistics & Monitoring

The system tracks:
- **Assignment Success Rate**: Projects successfully assigned
- **Timer Performance**: Runs, assignments made, errors
- **Resource Utilization**: Workload distribution across team
- **Processing Time**: How quickly projects get assigned

View stats with `/timer_status` in Discord.

## 🛡️ Safety Features

- **No Double Assignment**: Won't reassign existing assignments
- **Error Handling**: Continues processing even if one project fails
- **Permission Controls**: Role-based access to sensitive commands
- **Detailed Logging**: Comprehensive logs for debugging
- **Graceful Recovery**: Automatic retry and error reporting

## 🚨 Troubleshooting

### **Common Issues:**
1. **Import Errors**: Run from project root directory
2. **Sheet Access**: Check Google credentials and permissions
3. **Bot Offline**: Verify Discord token and internet connection
4. **No Assignments**: Check `READY_TO_ASSIGN` and `PROJECT_CONNECTED` columns

### **Logs Location:**
- Console output shows real-time status
- Check Discord notifications for assignment reports
- Use `/timer_status` for current system health

## 🎉 Benefits

✅ **Fully Automated**: No manual assignment needed  
✅ **Smart Matching**: Optimal resource allocation  
✅ **Real-time**: Processes new projects within 5 minutes  
✅ **Scalable**: Handles unlimited projects and team members  
✅ **Transparent**: Full visibility into assignments and performance  
✅ **Reliable**: Built-in error handling and recovery  

## 📄 License

MIT License - Software provided AS IS.

---

🚀 **Your project workflow is now fully automated!** Just keep the bot running and it will handle all new project assignments automatically.