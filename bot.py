import os
import discord
from discord.ext import commands

# === Variables d'environnement ===
TOKEN = os.getenv("DISCORD_TOKEN")

# === Intents / Bot ===
intents = discord.Intents.default()
intents.members = True  # important pour on_member_join
bot = commands.Bot(command_prefix="!", intents=intents)


# === Chargement des cogs ===
@bot.event
async def setup_hook():
    # Charger les cogs
    await bot.load_extension("cogs.welcome")
    await bot.load_extension("cogs.tickets")


# === Lancement du bot ===
if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN manquant dans les variables d'environnement.")
    bot.run(TOKEN)
