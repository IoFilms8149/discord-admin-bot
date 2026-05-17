import discord
from discord import app_commands
from discord.ext import commands, tasks
import math
from db import get_db
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with get_db() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS mod_logs (
                user_id INTEGER,
                name TEXT,
                action TEXT,
                guild_id INTEGER,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME
                )
            """)
            try:
                con.execute("ALTER TABLE mod_logs ADD COLUMN expires_at DATETIME")
            except:
                pass  # column already exists, ignore
            con.execute("""
                CREATE TABLE IF NOT EXISTS server_info (
                id INTEGER PRIMARY KEY, 
                name TEXT, 
                latency INTEGER,
                status TEXT DEFAULT "Offline",
                member_count INTEGER,
                role_count INTEGER,
                date_created TEXT
                )
            """)

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.ping.is_running():
            self.ping.start()
        if self.bot.guilds:
            name = self.bot.guilds[0].name
            with get_db() as con:
                con.execute(
                    "INSERT OR REPLACE INTO server_info (id, name) VALUES (1, ?)",
                    (name,)
                    )
        if not self.check_expired_bans.is_running():
            self.check_expired_bans.start()
    def cog_unload(self):
        self.ping.cancel()
        self.check_expired_bans.cancel()
    # Checks every 5 minutes
    @tasks.loop(minutes=5)
    async def check_expired_bans(self):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with get_db() as con:
            expired = con.execute(
                "SELECT user_id, guild_id FROM mod_logs WHERE action = 'Tempban' AND expires_at <= ? AND expires_at IS NOT NULL",
                (now,)
            ).fetchall()
        for row in expired:
            guild = self.bot.get_guild(row["guild_id"])
            if guild:
                try:
                    user = await self.bot.fetch_user(row["user_id"])
                    await guild.unban(user)
                    print(f"Auto-unbanned {user}")
                    with get_db() as con:
                        con.execute(
                            "UPDATE mod_logs SET expires_at = NULL WHERE user_id = ? AND action = 'Tempban'",
                            (row["user_id"],)
                        )
                except discord.NotFound:
                    with get_db() as con:
                        con.execute(
                            "UPDATE mod_logs SET expires_at = NULL WHERE user_id = ? AND action = 'Tempban'",
                            (row["user_id"],)
                        ) 
    @tasks.loop(seconds=60)
    async def ping(self):
        if not self.bot.is_ready() or math.isnan(self.bot.latency):
            return
        guild = self.bot.guilds[0]
        latency = round(self.bot.latency * 1000)
        member_count = guild.member_count
        roles = len(guild.roles)
        date = guild.created_at.strftime("%d %B %Y")
        with get_db() as con:
            con.execute("""
            UPDATE server_info 
            SET latency = ?, 
            status = 'Online', 
            member_count = ?,
            role_count = ?,
            date_created = ?
            WHERE id = 1""", (latency, member_count, roles, date,)
            )

    async def disconnect(self):
        with get_db() as con:
            con.execute("UPDATE server_info SET status = 'Offline' WHERE id = 1")
        
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
        with get_db() as con:
            con.execute("INSERT INTO mod_logs (user_id, name, guild_id, action, reason) VALUES (?, ?, ?, ?, ?)", (member.id, member.name, interaction.guild.id, "Warn", reason))
            warn_count = con.execute("SELECT COUNT(*) FROM mod_logs WHERE user_id = ? AND guild_id = ? AND action = 'Warn'", (member.id, interaction.guild.id)).fetchone()[0]
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
            expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()
            auto_ban = self.create_dm_embed("Automated Tempban", interaction.guild.name, auto_reason, discord.Color.dark_red(), duration=minutes)
            try:
                await member.send(embed=auto_ban)
            except:
                pass
            await member.ban(reason=auto_reason, delete_message_seconds=0)
            await interaction.channel.send(f"🚨{member.mention} has been automatically banned for 1 hour. (3+ warnings).")
            with get_db() as con:
                con.execute("INSERT INTO mod_logs (user_id, name, guild_id, action, reason, expires_at) VALUES (?, ?, ?, ?, ?, ?)", 
                            (member.id, member.name, interaction.guild.id, "Tempban", auto_reason, expires_at)
                        )
    # Kick Command
    @app_commands.command(name="kick", description="Kicks a member from the server.")
    @app_commands.describe(member="The user to kick", reason="The reason for the kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        with get_db() as con:
            con.execute("INSERT INTO mod_logs (user_id, name, guild_id, action, reason) VALUES (?, ?, ?, ?, ?)",
        (member.id, member.name, interaction.guild.id, "Kick", reason))
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
        expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)).isoformat()
        with get_db() as con:
            con.execute("INSERT INTO mod_logs (user_id, name, guild_id, action, reason, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
        (member.id, member.name, interaction.guild.id, "Tempban", reason, expires_at))
        await interaction.response.defer(ephemeral=True)
        dm_embed = self.create_dm_embed("Tempban", interaction.guild.name, reason, discord.Color.yellow(), duration=minutes)
        try:
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            print(f"Could not DM {member.display_name}")
        try:
            await member.ban(reason=reason, delete_message_seconds=3600)
            await interaction.followup.send(f"✅ Banned {member.display_name} for {minutes} minute(s)")
        except Exception as e:
            print(f"LOG ERROR: {e}")
            await interaction.followup.send(content=f"⚠️ An error occurred: {e}")
    # Ban Command
    @app_commands.command(name="ban", description="Bans a specific person.")
    @app_commands.describe(member="The member to ban", reason="Reason for the ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        with get_db() as con:
            con.execute("INSERT INTO mod_logs (user_id, name, guild_id, action, reason) VALUES (?, ?, ?, ?, ?)",
        (member.id, member.name, interaction.guild.id, "Ban", reason))
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
            with get_db() as con:
                con.execute("INSERT INTO mod_logs (user_id, name, guild_id, action, reason) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.name, interaction.guild.id, "Unban", "Staff revoked ban"))
        except discord.NotFound:
            await interaction.followup.send(content=f"⚠️ User ID does not exist.")
        except discord.Forbidden:
            await interaction.followup.send(content=f"⚠️ Insufficient permissions to unban.")
        except Exception as e:
            print(f"LOG ERROR: {e}")
            await interaction.followup.send(content=f"⚠️ An error occurred: {e}")
async def setup(bot):
    await bot.add_cog(Moderation(bot))

