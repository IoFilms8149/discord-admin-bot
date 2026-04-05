import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot and client instances
bot = commands.Bot(command_prefix="!", intents=intents)
# Define events and commands for the bot
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}")
        print(f"Successfully synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
#Ping Command
@bot.tree.command(name = "ping", description="Tells the latency (ms) of the bot")
async def ping(interatction: discord.Interaction):
    await interatction.response.send_message(f'Pong! :ping_pong: {bot.latency * 1000:.2f} ms')

# Kick command
@bot.tree.command(name="kick", description="Kicks a member from the server.")
@app_commands.describe(member="The user to kick", reason = "The reason for the kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await interaction.response.defer(ephemeral=True)
    target = str(member.display_name)
    try:
        await member.kick(reason=reason)
        await interaction.followup.send(f"✅ Sucessfully kicked **{target}**!")
        print(f"Terminal Log: Kicked {target}")
    except discord.Forbidden:
        await interaction.followup.send("❌ Not high enough permissions to kick that user.")
    except Exception as e:
        print(f"LOG ERROR: {e}") 
        await interaction.send(f"⚠️ An error occurred: {e}")
bot.run(BOT_TOKEN)
