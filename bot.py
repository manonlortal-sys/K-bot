import os
import discord
from discord.ext import commands

# === Variables d'environnement ===
TOKEN = os.getenv("DISCORD_TOKEN")

# === Intents / Bot ===
intents = discord.Intents.default()
intents.members = True  # important pour on_member_join
intents.message_content = True  # utile si tu gardes des commandes prefix "!"

bot = commands.Bot(command_prefix="!", intents=intents)


# === Chargement des cogs et sync des commandes slash ===
async def setup_hook():
    await bot.load_extension("cogs.welcome")
    await bot.load_extension("cogs.tickets")

    # Synchronisation globale des slash commands
    await bot.tree.sync()
    print("Slash commands synchronisées.")


bot.setup_hook = setup_hook


# === Lancement du bot ===
if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN manquant dans les variables d'environnement.")
    bot.run(TOKEN)
