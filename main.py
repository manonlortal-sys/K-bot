import sys
import threading
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, INSCRIPTION_CHANNEL, TEAMS_CHANNEL
from web.flask_app import app
from views.inscription_view import InscriptionView

# =========================
# AUDIOOP FIX
# =========================
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop
    sys.modules["audioop"] = audioop

# =========================
# FLASK
# =========================
def run_flask():
    app.run(host="0.0.0.0", port=10000)

# =========================
# BOT
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot.teams = []

# =========================
# EMBED FUNCTION
# =========================
async def update_teams_embed():
    channel = bot.get_channel(TEAMS_CHANNEL)

    if not channel:
        print("Salon teams introuvable")
        return

    embed = discord.Embed(
        title="ÉQUIPES DU TOURNOI",
        color=0x9b59b6
    )

    if len(bot.teams) == 0:
        embed.description = "Aucune équipe inscrite."
    else:
        for i, t in enumerate(bot.teams, 1):
            embed.add_field(
                name=f"Équipe {i}",
                value=f"Capitaine: <@{t['capitaine']}>",
                inline=False
            )

    await channel.send(embed=embed)

# 🔥 ATTACHE LA FONCTION AU BOT (IMPORTANT)
bot.update_teams_embed = update_teams_embed

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print(f"Bot connecté: {bot.user}")

    channel = bot.get_channel(INSCRIPTION_CHANNEL)

    if channel:
        embed = discord.Embed(
            title="TOURNOI DOFUS TOUCH",
            description="Clique sur Je participe",
            color=0x9b59b6
        )

        await channel.send(embed=embed, view=InscriptionView())

    await bot.update_teams_embed()

# =========================
# START
# =========================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)