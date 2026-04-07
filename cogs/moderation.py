import discord
import asyncio
from discord import app_commands
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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

            await asyncio.sleep(minutes * 60)
            await interaction.guild.unban(member)
            print(f"Terminal Log: Member {member.display_name} has been unbanned")
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

