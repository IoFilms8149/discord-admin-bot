import discord
from discord.ext import commands
from discord import app_commands
import random
from db import get_db

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #Balance Command
    @app_commands.command(name="balance", description="Check your current coin balance.")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        with get_db() as con:
            row = con.execute("SELECT balance FROM levels WHERE user_id = ?", (member.id,)).fetchone()

        bal = row[0] if row else 0
        if member == interaction.user:
            await interaction.response.send_message(f"You currently have **{bal}** coins!", ephemeral=True)
        else:
            await interaction.response.send_message(f"**{member.display_name}** currently has **{bal}** coins!", ephemeral=True)
    # Flip Coin Command
    @app_commands.command(name="flip", description="Bet your coins on a coin flip.")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def flip(self, interaction: discord.Interaction, amount: int, choice: str):
        if amount <= 0:
            await interaction.response.send_message("You must bet at least 1 coin!", ephemeral=True)
            return
        with get_db() as con:
            row = con.execute("SELECT balance FROM levels WHERE user_id = ?", (interaction.user.id,)).fetchone()

            current_bal = row[0] if row else 0
            if amount > current_bal:
                await interaction.response.send_message(
                    f"You don't have enough coins! Your current balance is {current_bal}",
                    ephemeral=True
                )
                return
            result = random.choice(["heads", "tails"])
            if choice == result:
                new_bal = current_bal + amount
                con.execute("UPDATE levels SET balance = ? WHERE user_id = ?", (new_bal, interaction.user.id,))
                await interaction.response.send_message(f"🪙  The coin landed on **{result}**! You won **{amount}** coins!")
            else:
                new_bal = current_bal - amount
                con.execute("UPDATE levels SET balance = ? WHERE user_id = ?", (new_bal, interaction.user.id))
                await interaction.response.send_message(f"🪙 The coin landed on **{result}**! You chose {choice} and lost.")
            

    # Daily Command
    @app_commands.command(name="daily", description="Claim free coins every 24 hours.")
    @app_commands.checks.cooldown(1, 84600, key=lambda i: i.user.id)
    async def daily(self, interaction: discord.Interaction):
        with get_db() as con:
            con.execute("INSERT OR IGNORE INTO levels (user_id) VALUES (?)", (interaction.user.id,))
            con.execute("UPDATE levels SET balance = balance + 100 WHERE user_id = ?", (interaction.user.id,))
        await interaction.response.send_message("You claimed your daily 100 coins! Come back in 24 hours for more.")
    @daily.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            hours = int(error.retry_after // 3600)
            minutes = int((error.retry_after % 3600) // 60)
            await interaction.response.send_message(
                f"Please come back later. Your next daily reward is in **{hours}** hours and **{minutes}** minutes.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Fun(bot))
