import discord
import asyncio
from discord import app_commands
from discord.ext import commands
import sqlite3

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.con = sqlite3.connect("users.db")
        self.cur = self.con.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
            user_id INTEGER,
            guild_id INTEGER,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.con.commit()
    def create_dm_embed(self, action, guild_name, reason, colour, duration = None):
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
    # Warn Command
    @app_commands.command(name="warn", description="Warn a member for breaking rules.")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(member="The user to warn", reason="Reason for the warn")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        self.cur.execute("INSERT INTO warnings (user_id, guild_id, reason) VALUES (?, ?, ?)",
        (member.id, interaction.guild.id, reason)
        )
        self.con.commit()
        self.cur.execute("SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?", 
        (member.id, interaction.guild.id)
        )
        warn_count = self.cur.fetchone()[0]
        dm_embed = self.create_dm_embed("Warn", interaction.guild.name, reason, discord.Color.orange())
        try:
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            print(f"Could not DM {member.display_name}")
        embed = discord.Embed(title="⚠️ User Warned", color=discord.Color.red())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Total Warnings", value=str(warn_count), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
        if warn_count >= 3:
            auto_reason = f"Automatic tempban: Reached {warn_count} warnings."
            minutes = 60
            auto_ban = self.create_dm_embed("Automated Tempban", interaction.guild.name, auto_reason, discord.Color.dark_red(), duration=minutes)
            try:
                await member.send(embed=auto_ban)
            except:
                pass
            await member.ban(reason=auto_reason, delete_message_seconds=0)
            await interaction.channel.send(f"🚨{member.mention} has been automatically banned for 1 hour. (3+ warnings).")
            async def run_unban():
                await asyncio.sleep(minutes * 60)
                await interaction.guild.unban(member)
                print(f"Terminal Log: {member.display_name} auto-unbanned.")
            asyncio.create_task(run_unban())
    # Kick Command
    @app_commands.command(name="kick", description="Kicks a member from the server.")
    @app_commands.describe(member="The user to kick", reason="The reason for the kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer(ephemeral=True)
        dm_embed = self.create_dm_embed("Kick", interaction.guild.name, reason, discord.Color.orange())
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
    # Clear Command
    @app_commands.command(name="clear", description="Clears a specified amount of messages.")
    @app_commands.describe(amount = "The amount of messages to be cleared")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.send_message(f"Clearing {amount} messages...", ephemeral=True)
        cleared = await interaction.channel.purge(limit=amount)
        try:
            await interaction.edit_original_response(content=f"✅ Successfully cleared {len(cleared)} message(s).")
        except Exception as e:
            print(f"LOG ERROR: {e}") 
            await interaction.followup.send(f"⚠️ An error occurred: {e}")
    # Tempban Command
    @app_commands.command(name="tempban", description="Bans a member for a set amount of time")
    @app_commands.checks.has_permissions(ban_members=True)
    async def tempban(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
        await interaction.response.defer(ephemeral=True)
        dm_embed = self.create_dm_embed("Tempban", interaction.guild.name, reason, discord.Color.yellow(), duration=minutes)
        try:
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            print(f"Could not DM {member.display_name}")
        try:
            await member.ban(reason=reason, delete_message_seconds=3600)
            await interaction.followup.send(f"✅ Banned {member.display_name} for {minutes} minute(s)")

            async def run_unban():
                await asyncio.sleep(minutes * 60)
                await interaction.guild.unban(member)
                print(f"Terminal Log: {member.display_name} auto-unbanned.")
                
            asyncio.create_task(run_unban())
        except Exception as e:
            print(f"LOG ERROR: {e}")
            await interaction.followup.send(content=f"⚠️ An error occurred: {e}")
    # Ban Command
    @app_commands.command(name="ban", description="Bans a specific person.")
    @app_commands.describe(member="The member to ban", reason="Reason for the ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer(ephemeral=True)
        target = str(member.display_name)
        dm_embed = self.create_dm_embed("Ban", interaction.guild.name, reason, discord.Color.red())
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
    # Unban Command
    @app_commands.command(name="unban", description="Unbans a banned member.")
    @app_commands.describe(user_id="The ID of the member you want to unban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        await interaction.response.defer(ephemeral=True)
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.followup.send(content=f"✅Unbanned {user.name}")
            print(f"Terminal Log: Unbanned {user.name}")
        except Exception as e:
            print(f"LOG ERROR: {e}")
            await interaction.followup.send(content=f"⚠️ An error occurred: {e}")
async def setup(bot):
    await bot.add_cog(Moderation(bot))

