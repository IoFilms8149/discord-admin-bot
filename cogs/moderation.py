import discord
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
import sqlite3
import math
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ping.start()
        self.con = sqlite3.connect("users.db")
        self.cur = self.con.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS mod_logs (
            user_id INTEGER,
            action TEXT,
            guild_id INTEGER,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.con.commit()
    @commands.Cog.listener()
    async def on_ready(self):
        con = sqlite3.connect("users.db")
        con.execute("""CREATE TABLE IF NOT EXISTS server_info (
            id INTEGER PRIMARY KEY, 
            name TEXT, 
            latency INTEGER,
            status TEXT DEFAULT "Offline",
            member_count INTEGER,
            role_count INTEGER,
            date_created TEXT
            )
        """)
        if self.bot.guilds:
            name = self.bot.guilds[0].name
            con.execute("INSERT OR REPLACE INTO server_info (id, name) VALUES (1, ?)", (name,))
        con.commit()
        con.close()
    @tasks.loop(seconds=60)
    async def ping(self):
        if not self.bot.is_ready() or math.isnan(self.bot.latency):
            return
        guild = self.bot.guilds[0]
        latency = round(self.bot.latency * 1000)
        member_count = guild.member_count
        roles = len(guild.roles)
        date = guild.created_at.strftime("%d %B %Y")
        con = sqlite3.connect("users.db")
        con.execute("""
        UPDATE server_info 
        SET latency = ?, 
        status = 'Online', 
        member_count = ?,
        role_count = ?,
        date_created = ?
        WHERE id = 1""", (latency, member_count, roles, date)
        )
        con.commit()
        con.close()
    async def disconnect(self):
        con = sqlite3.connect("users.db")
        con.execute("UPDATE server_info SET status = 'Offline' WHERE id = 1")
        con.commit()
        con.close()
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
        self.cur.execute("INSERT INTO mod_logs (user_id, guild_id, action, reason) VALUES (?, ?, ?, ?)",
        (member.id, interaction.guild.id, "Warn", reason)
        )
        self.con.commit()
        self.cur.execute("SELECT COUNT(*) FROM mod_logs WHERE user_id = ? AND guild_id = ?", 
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
        self.cur.execute("INSERT INTO mod_logs (user_id, guild_id, action, reason) VALUES (?, ?, ?, ?)",
        (member.id, interaction.guild.id, "Kick", reason))
        self.con.commit()
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
        self.cur.execute("INSERT INTO mod_logs (user_id, guild_id, action, reason) VALUES (?, ?, ?, ?)",
        (member.id, interaction.guild.id, "Tempban", reason))
        self.con.commit()
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
        self.cur.execute("INSERT INTO mod_logs (user_id, guild_id, action, reason) VALUES (?, ?, ?, ?)",
        (member.id, interaction.guild.id, "Ban", reason))
        self.con.commit()
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
        self.cur.execute("INSERT INTO mod_logs (user_id, guild_id, action, reason) VALUES (?, ?, ?, ?)",
        (user_id, interaction.guild.id, "Unban", "Staff revoked ban"))
        self.con.commit()
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

