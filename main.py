import discord
from discord.ext import commands
import os

from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    print("🎮 Tournoi bot prêt")


# Chargement futur des modules
async def load_extensions():
    # On ajoutera les cogs progressivement
    pass


if __name__ == "__main__":
    bot.run(TOKEN)
