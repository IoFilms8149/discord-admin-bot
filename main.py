import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("hello"):
        await message.channel.send("Hello!")
    
client.run(BOT_TOKEN)
