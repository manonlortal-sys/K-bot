import discord
from discord.ext import commands
import threading

from config import DISCORD_TOKEN, INSCRIPTION_CHANNEL
from web.flask_app import app
from views.inscription_view import InscriptionView

# 🔥 Désactive voice (évite audioop)
discord.VoiceClient = None

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def run_flask():
    port = 10000
    app.run(host="0.0.0.0", port=port)


@bot.event
async def on_ready():
    print(f"Bot connecté: {bot.user}")

    channel = bot.get_channel(INSCRIPTION_CHANNEL)

    if channel:
        embed = discord.Embed(
            title="TOURNOI DOFUS TOUCH",
            description="Clique sur 🎮 Je participe",
            color=0x9b59b6
        )

        await channel.send(embed=embed, view=InscriptionView())


bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()