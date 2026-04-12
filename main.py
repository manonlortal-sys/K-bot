import sys
import threading
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, INSCRIPTION_CHANNEL, TEAMS_CHANNEL
from web.flask_app import app
from views.inscription_view import InscriptionView

# =========================
# FIX AUDIOOP (Python 3.13)
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
# UPDATE TEAMS EMBED (FIXÉ)
# =========================
async def update_teams_embed():
    try:
        channel = await bot.fetch_channel(TEAMS_CHANNEL)

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

    except Exception as e:
        print(f"Erreur update embed teams: {e}")

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

    await update_teams_embed()

# =========================
# START
# =========================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)