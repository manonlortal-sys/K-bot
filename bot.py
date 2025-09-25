import os
import discord
from discord.ext import commands

# === Variables d'environnement ===
TOKEN = os.getenv("DISCORD_TOKEN")

# === Intents / Bot ===
intents = discord.Intents.default()
intents.members = True  # important pour on_member_join
intents.message_content = True  # utile si tu veux encore utiliser des commandes prefix "!"

bot = commands.Bot(command_prefix="!", intents=intents)


# === Chargement des cogs ===
async def setup_hook():
    await bot.load_extension("cogs.welcome")
    await bot.load_extension("cogs.tickets")


# On attache la fonction setup_hook personnalisée à l’instance du bot
bot.setup_hook = setup_hook


# === Lancement du bot ===
if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN manquant dans les variables d'environnement.")
    bot.run(TOKEN)
