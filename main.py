import discord
import asyncio
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import sqlite3

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
class MyBot(commands.Bot):
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        await self.load_extension("cogs.utility")
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.stats")
        try:
            synced = await self.tree.sync()
            print(f"Successfully synced {len(synced)} commands.")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
    async def on_ready(self):
        print(f"Logged in as {self.user}")
bot = MyBot()
bot.run(BOT_TOKEN)
