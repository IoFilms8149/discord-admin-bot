# Discord Admin Bot

This is a discord bot built using `discord.py` designed for server moderation.

## Features

- **Secure Bot Configuration**: Uses `python-dotenv` to keep your bot token private.
- **Latency Tracking**: Has a `/ping` command to check bot responsiveness.
- **Moderation Commands**: 
   * `/kick` & `/ban` with automated embedded DM notifications.
   * `/clear` for quick channel cleanup.

## Requirements:

- **Python 3.12**: The main language for the bot.
- **discord.py**: The Python library used to interact with Discord.
- **python-dotenv**: Used to secure your bot token.
- **asyncio**: Powers the bot with moderation timers.

## Setup:
1. **Clone the repo** (or download the files).
2. **Install the requirements**: 
   Run `pip install -r requirements.txt`
3. **Set up your bot token**:
   Create a file named `.env` and paste your token inside:
   `TOKEN=your_token_here`
4. **Start the bot**:
   `python main.py`

