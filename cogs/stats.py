import discord
from discord import app_commands
from discord.ext import commands
from db import get_db

class leaderboarview(discord.ui.View):
    def __init__(self, bot, total_pages):
        super().__init__(timeout=60)
        self.bot = bot
        self.current_page = 0
        self.total_pages = total_pages
    async def get_page_embed(self):
        offset = self.current_page * 10
        with get_db() as con:
            data = con.execute("SELECT username, xp FROM levels ORDER BY xp DESC LIMIT 10 OFFSET ?", (offset,)).fetchall()
        embed = discord.Embed(
            title="🏆 Server Leaderboard:",
            description=f"Top Members (Page {self.current_page + 1})",
            color=discord.Color.gold(),
            )
        if not data:
                embed.description = "No more users found on this page."
        else:
                for index, (name, xp) in enumerate(data):
                    rank = index + 1 + offset
                    embed.add_field(name=f"{rank}. {name}", value=f"{xp} XP", inline=False)
            
        return embed

    @discord.ui.button(label="Back", style=discord.ButtonStyle.gray)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.get_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You're already on the first page!", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        embed = await self.get_page_embed()
        if "No more users" in embed.description:
            self.current_page -= 1
            await interaction.response.send_message("No more pages available!", ephemeral=True)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Connects to database
        with get_db() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS levels (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    avatar_url TEXT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    balance INTEGER DEFAULT 100
                )
            """)
    @commands.Cog.listener()
    async def on_message(self, message):
        # Adds 5 XP when an user sends a message
        if message.author.bot:
            return
        user_id = message.author.id
        username = message.author.name
        balance = 100
        avatar_url = str(message.author.avatar.url) if message.author.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
        with get_db() as con:
            con.execute("UPDATE LEVELS SET avatar_url = ? WHERE user_id = ?", (avatar_url, user_id,))
            con.execute("""
                INSERT INTO levels (user_id, username, xp, balance) 
                VALUES (?, ?, 5, 100) 
                ON CONFLICT(user_id) DO UPDATE SET 
                xp = xp + 5, 
                username = excluded.username
            """, (user_id, username))

            row = con.execute("SELECT xp, level FROM levels WHERE user_id = ?", (user_id,)).fetchone()
        xp, level = row["xp"], row["level"]
        # Levels a member up
        new_level = 5 * (level ** 2) + 50 * level + 100
        if xp >= new_level:
            actual_new_level = level + 1
            with get_db() as con:
                con.execute("UPDATE levels SET level = ? WHERE user_id = ?", (actual_new_level, user_id,))

            await message.channel.send(f"{message.author.mention} has leveled up to **Level {actual_new_level}**!")
    # Checks the user's rank
    @app_commands.command(name="rank", description="Checks your current XP and level")
    async def rank(self, interaction: discord.Interaction):
        with get_db() as con:
            result = con.execute("SELECT xp, level FROM levels WHERE user_id = ?", (interaction.user.id,)).fetchone()
        if result:
            xp, level = result
            await interaction.response.send_message(f"**{interaction.user.display_name}**, you are **Level {level}** with **{xp} XP**!")
        else:
            await interaction.response.send_message("You haven't sent any messages yet!")
    @app_commands.command(name="leaderboard", description="Check which members have the highest amount of XP")
    async def leaderboard(self, interaction: discord.Interaction):
        with get_db() as con:
            total_users = con.execute("SELECT COUNT(*) FROM levels").fetchone()[0]
        total_pages = (total_users - 1) // 10 + 1 if total_users > 0 else 1
        view = leaderboarview(self.bot, total_pages)
        embed = await view.get_page_embed()
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Stats(bot))