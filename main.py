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
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! :ping_pong: {bot.latency * 1000:.2f} ms')

# Kick command
@bot.tree.command(name="kick", description="Kicks a member from the server.")
@app_commands.describe(member="The user to kick", reason = "The reason for the kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await interaction.response.defer(ephemeral=True)
    target = str(member.display_name)
    try:
        await member.kick(reason=reason)
        await interaction.followup.send(f"✅ Successfully kicked **{target}**!")
        print(f"Terminal Log: Kicked {target}")
    except discord.Forbidden:
        await interaction.followup.send("❌ Not high enough permissions to kick that user.")
    except Exception as e:
        print(f"LOG ERROR: {e}") 
        await interaction.followup.send(f"⚠️ An error occurred: {e}")

# Clear command
@bot.tree.command(name="clear", description="Clears a specified amount of messages.")
@app_commands.describe(amount = "The amount of messages to be cleared")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.send_message(f"Clearing {amount} messages...", ephemeral=True)
    cleared = await interaction.channel.purge(limit=amount)
    try:
        await interaction.edit_original_response(content=f"✅ Successfully cleared {len(cleared)} messages.")
    except Exception as e:
        print(f"LOG ERROR: {e}") 
        await interaction.followup.send(f"⚠️ An error occurred: {e}")
# Ban Command
@bot.tree.command(name="ban", description="Bans a specific person.")
@app_commands.describe(member="The member to ban", reason="Reason for the ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await interaction.response.defer(ephemeral=True)
    target = str(member.display_name)

    try:
        await member.ban(reason=reason, delete_message_seconds=3600)
        await interaction.followup.send(content=f"✅Successfully banned **{target}**.")
        print(f"Terminal log: Banned {target}")
    except Exception as e:
        print(f"LOG ERROR: {e}")
        await interaction.followup.send(content=f"⚠️ An error occurred: {e}")
#Unban Command
@bot.tree.command(name="unban", description="Unbans a banned member.")
@app_commands.describe(user_id="The ID of the member you want to unban")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer(ephemeral=True)
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.followup.send(content=f"✅Unbanned {user.name}")
    except Exception as e:
        print(f"LOG ERROR: {e}")
        await interaction.followup.send(content=f"⚠️ An error occurred: {e}")

bot.run(BOT_TOKEN)
