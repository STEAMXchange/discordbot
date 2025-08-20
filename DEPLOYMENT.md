# Deployment Guide

This guide covers deploying the SteamXQuality bot on different platforms.

## Local Development

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser
- Discord Bot Token
- Google Sheets API credentials

### Setup
1. Clone the repository
2. Run `python setup.py`
3. Edit `.env` with your configuration
4. Run `python qc.py`

## Linux Server Deployment

### Using systemd (Recommended)

1. **Create a systemd service file**
   ```bash
   sudo nano /etc/systemd/system/steamxquality.service
   ```

2. **Add the following content:**
   ```ini
   [Unit]
   Description=SteamXQuality Discord Bot
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/steamxquality
   Environment=PATH=/path/to/steamxquality/venv/bin
   ExecStart=/path/to/steamxquality/venv/bin/python qc.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable steamxquality
   sudo systemctl start steamxquality
   ```

4. **Check status:**
   ```bash
   sudo systemctl status steamxquality
   ```

### Using the provided script

The `steamxqualityauto.sh` script can be used for basic deployment:

```bash
chmod +x steamxqualityauto.sh
./steamxqualityauto.sh
```

## Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.9-slim

# Install Chrome dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Run the bot
CMD ["python", "qc.py"]
```

### Build and run

```bash
# Build the image
docker build -t steamxquality .

# Run the container
docker run -d \
  --name steamxquality-bot \
  --env-file .env \
  steamxquality
```

## Windows Server Deployment

### Using Windows Task Scheduler

1. **Create a batch file** (`start_bot.bat`):
   ```batch
   @echo off
   cd /d "C:\path\to\steamxquality"
   python qc.py
   pause
   ```

2. **Set up Task Scheduler:**
   - Open Task Scheduler
   - Create Basic Task
   - Set trigger to "At startup"
   - Action: Start a program
   - Program: `C:\path\to\steamxquality\start_bot.bat`
   - Check "Run with highest privileges"

### Using Windows Service

Use a tool like NSSM to create a Windows service:

```bash
nssm install SteamXQuality "C:\path\to\python.exe" "C:\path\to\steamxquality\qc.py"
nssm set SteamXQuality AppDirectory "C:\path\to\steamxquality"
nssm start SteamXQuality
```

## Cloud Deployment

### Heroku

1. **Create `Procfile`:**
   ```
   worker: python qc.py
   ```

2. **Create `runtime.txt`:**
   ```
   python-3.9.18
   ```

3. **Deploy:**
   ```bash
   heroku create your-app-name
   heroku config:set DISCORD_BOT_TOKEN=your_token
   heroku config:set QC_ROLE_ID=your_role_id
   # ... set other environment variables
   git push heroku main
   ```

### Railway

1. **Connect your GitHub repository**
2. **Set environment variables in Railway dashboard**
3. **Deploy automatically on push**

### DigitalOcean App Platform

1. **Create app from GitHub repository**
2. **Set environment variables**
3. **Configure build command:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure run command:**
   ```bash
   python qc.py
   ```

## Environment Variables

Make sure to set these environment variables in your deployment platform:

- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `QC_ROLE_ID` - Discord role ID for QC permissions
- `GOOGLE_CREDENTIALS_FILE` - Path to Google credentials JSON
- `PROJECT_SHEET_NAME` - Google Sheets project sheet name
- `MANAGEMENT_SHEET_NAME` - Google Sheets management sheet name
- `FORUM_CHANNEL_ID` - Discord forum channel ID
- `PASS_TAG_ID` - Discord forum tag ID for pass
- `FAIL_TAG_ID` - Discord forum tag ID for fail
- `STALLED_TAG_ID` - Discord forum tag ID for stalled

## Monitoring and Logs

### Log Management

- **Local/Server**: Check console output or systemd logs
- **Docker**: `docker logs steamxquality-bot`
- **Cloud**: Use platform-specific logging (Heroku logs, Railway logs, etc.)

### Health Checks

The bot provides console output for monitoring:
- Startup messages
- Thread registration/unregistration
- QC processing results
- Error messages

### Restart Policies

- **systemd**: Automatic restart on failure
- **Docker**: Use `--restart=always` flag
- **Cloud**: Most platforms auto-restart on crashes

## Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **Google Credentials**: Keep JSON files secure
3. **Discord Token**: Rotate tokens regularly
4. **Network Security**: Use HTTPS for all external connections
5. **Access Control**: Limit server access to authorized personnel

## Troubleshooting

### Common Issues

1. **Chrome/Chromium not found**: Install browser or use Docker
2. **Permission denied**: Check file permissions and user access
3. **Port conflicts**: Ensure no other services use required ports
4. **Memory issues**: Monitor resource usage, especially for web scraping

### Debug Mode

Add debug logging by modifying the bot code:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support

For deployment issues:
- Check platform-specific documentation
- Review environment variable configuration
- Verify all dependencies are installed
- Check network connectivity and firewall settings
