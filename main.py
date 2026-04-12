import sys

# =========================
# HACK audioop (Python 3.13)
# =========================
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop
    sys.modules["audioop"] = audioop

import threading
import discord
from discord.ext import commands

from config import (
    DISCORD_TOKEN,
    INSCRIPTION_CHANNEL,
)
from web.flask_app import app
from views.inscription_view import InscriptionView

# =========================
# FLASK
# =========================
def run_flask():
    app.run(host="0.0.0.0", port=10000)

# =========================
# DISCORD BOT
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# stockage équipes
bot.teams = []

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
            description="Clique sur Je participe pour inscrire ton équipe",
            color=0x9b59b6
        )

        await channel.send(embed=embed, view=InscriptionView())

# =========================
# START
# =========================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)