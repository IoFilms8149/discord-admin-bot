# Discord Admin Bot

This is a discord bot built using `discord.py` and `SQLite3` designed for server moderation. It includes dashboard using `flask` to monitor the bot.

## Features

- **Secure Bot Configuration**: Uses `python-dotenv` to keep your bot token private.
- **Latency Tracking**: Has a `/ping` command to check bot responsiveness.
- **Leveling System**: Tracks users XP stored in a SQLite database.
- **Dashboard**: Includes a dashboard that monitors the discord bot and server.
- **Moderation Commands**: 
   * `/kick` & `/ban` with automated embedded DM notifications.
   * `/clear` for quick channel cleanup.

## Requirements:

- **Python 3.12**: The main language for the bot.
- **discord.py**: The Python library used to interact with Discord.
- **python-dotenv**: Used to secure your bot token.
- **asyncio**: Powers the bot with moderation timers.
- **SQLite3**: Database to store the user's data.
- **flask**: A Python library that tracks the bot in the dashboard.

## Setup:
### Running the bot:
1. **Clone the repo** (or download the files).
2. **Install the requirements**: 
   Run `pip install -r requirements.txt`
3. **Set up your bot token**:
   Create a file named `.env` and paste your token inside:
   `TOKEN=your_token_here`
4. **Start the bot**:
   `python main.py`
### Opening the dashboard:
1. **Start the dashboard**:
   Run `python web_app.py`
2. **Open the dashboard on a browser**:
   Go to http://127.0.0.1:5000

