import discord
from discord import app_commands
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # Ping Command
    @app_commands.command(name="ping", description="Tells the latency (ms) of the bot")
    async def ping(self, interaction:discord.Interaction):
        await interaction.response.send_message(f'Pong! :ping_pong: {self.bot.latency * 1000:.2f} ms')
    # User Info Command
    @app_commands.command(name="userinfo", description="Shows information about a member.")
    @app_commands.describe(member="The member you want information about.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
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
    # Help Command
    @app_commands.command(name="help", description="Provides a list with a description of each command")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="**ADMIN BOT HELP MENU**",
            description="Here is a list of all available commands",
            color=discord.Colour.blue()
            )
        embed.add_field(name="/ban [member] [reason]", value="Bans a member from the server.", inline=False)
        embed.add_field(name="/clear [amount]", value="Deletes a certaina amount of messages.", inline=False)
        embed.add_field(name="/kick [member] [reason]", value="Kicks a member from the server.", inline=False)
        embed.add_field(name="/rank", value="Checks the user's XP and level.", inline=False)
        embed.add_field(name="/ping", value="Check the bot's latency.", inline=False)
        embed.add_field(name="/tempban [member] [minutes] [reason]", value="Temporarily bans a member for a set amount of time", inline=False) 
        embed.add_field(name="/unban [user_id]", value="Unbans an already banned member.", inline=False)
        embed.add_field(name="userinfo [member]", value="Gets information about a member and their roles.", inline=False)
        await interaction.response.send_message(embed=embed)
    # Server Info Command
    @app_commands.command(name="serverinfo", description="Displays information about the server.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"Server Information: {guild.name}",
            color=discord.Color.blue()
        )
        created_date = guild.created_at.strftime("%d/%m/%y")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=False)
        embed.add_field(name="Members", value=guild.member_count, inline=False)
        embed.add_field(name="Roles", value=len(guild.roles), inline=False)
        embed.add_field(name="Created on:", value=created_date, inline=False)
        embed.set_footer(text=f"Server ID: {guild.id}")
        await interaction.response.send_message(embed=embed)
async def setup(bot):
    await bot.add_cog(Utility(bot))
