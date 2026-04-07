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
        self.cur.execute("""
        INSERT INTO levels (user_id, xp) VALUES (?, 5) ON CONFLICT(user_id) DO UPDATE SET xp = xp + 5
        """, (user_id,))
        self.con.commit()

        self.cur.execute("SELECT xp, level FROM levels WHERE user_id = ?", (user_id,))
        xp, level = self.cur.fetchone()
        # Levels a member up
        new_level = xp // 100
        if new_level > level:
            self.cur.execute("UPDATE levels SET level = ? WHERE user_id = ?", (new_level, user_id))
            self.con.commit()

            await message.channel.send(f"{message.author.mention} has leveled up to **Level {new_level}**!")
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

async def setup(bot):
    await bot.add_cog(Stats(bot))