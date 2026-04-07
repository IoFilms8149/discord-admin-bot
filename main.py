import discord
import asyncio
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

# Create DM embed when banned, tempbanned, or kicked
def create_dm_embed(action, guild_name, reason, colour, duration=None):
    embed = discord.Embed(
        title=f"⚠️ {action} Notification",
        description=f"This message is to notify you of a formal moderation action taken within **{guild_name}**.",
        color=colour
    )
    if duration:
        embed.add_field(name="Duration:", value=f"{duration} minute(s)", inline=False)
    embed.add_field(name="Reason:", value=reason, inline=False)
    embed.set_footer(text="Please contact an admin if you believe this was an error.")
    return embed

# Define events and commands for the bot
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}")
        print(f"Successfully synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
# Help Command
@bot.tree.command(name="help", description="Provides a list with a description of each command")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="**ADMIN BOT HELP MENU**",
        description="Here is a list of all available commands",
        color=discord.Colour.blue()
        )
    embed.add_field(name="/ban [member] [reason]", value="Bans a member from the server.", inline=False)
    embed.add_field(name="/clear [amount]", value="Deletes a certaina amount of messages.", inline=False)
    embed.add_field(name="/kick [member] [reason]", value="Kicks a member from the server.", inline=False)
    embed.add_field(name="/ping", value="Check the bot's latency.", inline=False)
    embed.add_field(name="/tempban [member] [minutes] [reason]", value="Temporarily bans a member for a set amount of time", inline=False) 
    embed.add_field(name="/unban [user_id]", value="Unbans an already banned member.", inline=False)
    embed.add_field(name="userinfo [member]", value="Gets information about a member and their roles.", inline=False)
    await interaction.response.send_message(embed=embed)
# Ping Command
@bot.tree.command(name="ping", description="Tells the latency (ms) of the bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! :ping_pong: {bot.latency * 1000:.2f} ms')
# User Info Command
@bot.tree.command(name="userinfo", description="Shows information about a member.")
@app_commands.describe(member="The member you want information about.")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    roles = [
    role.mention for role in reversed(member.roles) 
    if role.id != interaction.guild.id and role.name != "@everyone" and role.name != "everyone"
    ]   
    role_string = ", ".join(roles) if roles else "No roles assigned"
    embed = discord.Embed(
        title=f"User Info - {member.display_name}",
        color=member.color
    )
    embed.set_thumbnail(url=member.display_name if not member.avatar else member.avatar.url)
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Top Role", value=member.top_role.mention, inline=False)
    embed.add_field(name=f"Roles: {len(roles)}", value=role_string, inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)
# Kick command
@bot.tree.command(name="kick", description="Kicks a member from the server.")
@app_commands.describe(member="The user to kick", reason="The reason for the kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await interaction.response.defer(ephemeral=True)
    dm_embed = create_dm_embed("Kick", interaction.guild.name, reason, discord.Color.orange())
    target = str(member.display_name)
    try:
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        print(f"Could not DM {member.display_name}")
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
# Tempban Command
@bot.tree.command(name="tempban", description="Bans a member for a set amount of time")
async def tempban(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
    await interaction.response.defer(ephemeral=True)
    dm_embed = create_dm_embed("Tempban", interaction.guild.name, reason, discord.Color.yellow(), duration=minutes)
    try:
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        print(f"Could not DM {member.display_name}")
    try:
        await member.ban(reason=reason, delete_message_seconds=3600)
        await interaction.followup.send(f"✅ Banned {member.display_name} for {minutes} minute(s)")

        await asyncio.sleep(minutes * 60)
        await interaction.guild.unban(member)
        print(f"Terminal Log: Member {member.display_name} has been unbanned")
    except Exception as e:
        print(f"LOG ERROR: {e}")
        await interaction.followup.send(content=f"⚠️ An error occurred: {e}")
# Ban Command
@bot.tree.command(name="ban", description="Bans a specific person.")
@app_commands.describe(member="The member to ban", reason="Reason for the ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await interaction.response.defer(ephemeral=True)
    target = str(member.display_name)
    dm_embed = create_dm_embed("Ban", interaction.guild.name, reason, discord.Color.red())
    try:
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        print(f"Could not DM {member.display_name}")
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
        print(f"Terminal Log: Unbanned {user.name}")
    except Exception as e:
        print(f"LOG ERROR: {e}")
        await interaction.followup.send(content=f"⚠️ An error occurred: {e}")

bot.run(BOT_TOKEN)
