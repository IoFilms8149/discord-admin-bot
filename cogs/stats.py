import discord
from discord import app_commands
from discord.ext import commands
import sqlite3


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Connects to database
        self.con = sqlite3.connect("users.db")
        self.cur = self.con.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS levels (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        """)
        self.con.commit()
    @commands.Cog.listener()
    async def on_message(self, message):
        # Adds 5 XP when an user sends a message
        if message.author.bot:
            return
        user_id = message.author.id
        username = message.author.name
        self.cur.execute("""
        INSERT INTO levels (user_id, username, xp) VALUES (?, ?, 5) ON CONFLICT(user_id) DO UPDATE SET xp = xp + 5, username = excluded.username
        """, (user_id, username))
        self.con.commit()

        self.cur.execute("SELECT xp, level FROM levels WHERE user_id = ?", (user_id,))
        xp, level = self.cur.fetchone()
        # Levels a member up
        new_level = 5 * (level ** 2) + 50 * level + 100
        if xp >= new_level:
            actual_new_level = level + 1
            self.cur.execute("UPDATE levels SET level = ? WHERE user_id = ?", (actual_new_level, user_id,))
            self.con.commit()

            await message.channel.send(f"{message.author.mention} has leveled up to **Level {actual_new_level}**!")
    # Checks the user's rank
    @app_commands.command(name="rank", description="Checks your current XP and level")
    async def rank(self, interaction: discord.Interaction):
        self.cur.execute("SELECT xp, level FROM levels WHERE user_id = ?", (interaction.user.id,))
        result = self.cur.fetchone()
        if result:
            xp, level = result
            await interaction.response.send_message(f"**{interaction.user.display_name}**, you are **Level {level}** with **{xp} XP**!")
        else:
            await interaction.response.send_message("You haven't sent any messages yet!")
    @app_commands.command(name="leaderboard", description="Shows the top 10 users with the highest XP")
    async def leaderboard(self, interaction: discord.Interaction):
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        cur.execute("""SELECT user_id, xp, level FROM levels ORDER BY xp DESC LIMIT 10""")
        rows = cur.fetchall()
        con.close()

        embed = discord.Embed(
            title="🏆 Server Leaderboard:",
            color=discord.Color.blue()
        )
        description = ""
        for i, row in enumerate(rows, start=1):
            user_id, xp, level = row
            member = interaction.guild.get_member(user_id)
            name = member.display_name if member else f"User {user_id}"
            description += f"**{i}. {name}:** Level {level} ({xp} XP)\n"
        embed.description = description
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))