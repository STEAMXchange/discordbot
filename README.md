# SteamXQuality - Discord Quality Control Bot

A Discord bot that automates quality control processes for design projects, integrating with Google Sheets and Canva for seamless workflow management.

## Features

- **Automated QC Processing**: Automatically analyzes Canva designs for font consistency and color compliance
- **Google Sheets Integration**: Syncs project data, designer assignments, and QC results
- **Discord Forum Management**: Handles forum posts, thread creation, and automatic tagging
- **Permission System**: Role-based access control for different departments
- **Auto-Expiration**: Automatically marks old threads as failed after 30 days
- **Manual Override**: Support for manual QC review when needed

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Google Sheets API credentials
- Chrome/Chromium browser (for web scraping)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/STEAMXchange/discordbot.git
   cd discordbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a .env file. (See config below)

4. **Set up Google Sheets API**
   - Create a Google Cloud Project
   - Enable Google Sheets API
   - Create a service account and download the JSON credentials file
   - Place the credentials file in the project root
   - Update the `GOOGLE_CREDENTIALS_FILE` in your `.env`

5. **Configure Discord Bot**
   - Create a Discord application and bot
   - Enable required intents (Guilds, Members, Message Content, Messages)
   - Add the bot to your server with appropriate permissions
   - Update the `DISCORD_BOT_TOKEN` in your `.env`

## Configuration

Create a `.env` file in the project root
You can use the .env.example to see what you need to setup.

## Usage

### Starting the Bot

```bash
python qc.py
```

### Discord Commands

**Project Management:**
- `/register <project_id>` - Link a thread to a project ID
- `/unregister` - Unlink a thread from its project
- `/getprojectid` - Get the project ID linked to this thread
- `/whereisproject <project_id>` - Find the thread/location of a project ID
- `/getprojectinfo <project_id>` - Get detailed info about a project ID
- `/getUrl` - Get the Canva URL for this thread's project

**Quality Control:**
- `/status` - Check which project a thread is linked to
- `/mark <result> [reason]` - Mark QC result (PASS/FAIL)
- `/qc <url>` - Manually run QC on a Canva URL
- `/palette <image>` - Extract color palette from an image

**Permissions Required:**
- Most commands require QC role or manage messages permission
- `/register`, `/mark`, `/unregister` require special permissions

### Forum Post Requirements

When posting in the designated forum channel, include:

1. **Project ID**: Format `#000001` or `projectId: 000001`
2. **Canva Link**: Direct link to the Canva design
3. **Thumbnail**: Image attachment (required)
4. **Override Option**: Add `|| --OVERRIDE ||` to skip automated QC

### Quality Control Process

1. **Automatic Detection**: Bot detects new forum posts
2. **Validation**: Checks project ID, designer permissions, and Canva link
3. **Analysis**: Extracts text and font data from Canva design
4. **Scoring**: Evaluates font consistency and color compliance
5. **Reporting**: Generates detailed QC report
6. **Integration**: Updates Google Sheets with results

## File Structure

```
steamxquality/
├── qc.py                 # Main Discord bot application
├── sheets.py            # Google Sheets integration
├── requirements.txt     # Python dependencies
├── setup.py             # Setup and configuration script
├── .env                 # Environment variables (create from env.example)
├── env.example          # Example environment configuration
├── .gitignore           # Git ignore rules
├── steamxqualityauto.sh # Linux startup script
└── README.md            # This file
```
## Troubleshooting

### Common Issues

1. **Bot not responding**: Check Discord token and bot permissions
2. **Sheets access denied**: Verify Google credentials and API permissions
3. **Chrome driver issues**: Ensure Chrome/Chromium is installed
4. **Permission errors**: Check role IDs and bot permissions

### Logs

The bot provides detailed console output for debugging:
- Thread registration/unregistration
- QC processing results
- Error messages and warnings
- Auto-expiration notifications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT LICENSE
Software is provided AS IS.
