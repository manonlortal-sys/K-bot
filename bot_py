import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN", "TON_TOKEN_ICI")  # Placeholder

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté !")

bot.run(TOKEN)

