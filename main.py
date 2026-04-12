import discord
from discord.ext import commands
import threading

from config import DISCORD_TOKEN, INSCRIPTION_CHANNEL
from web.flask_app import app
from views.inscription_view import InscriptionView

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def run_flask():
    app.run(host="0.0.0.0", port=10000)


@bot.event
async def on_ready():
    print("Bot OK")

    channel = bot.get_channel(INSCRIPTION_CHANNEL)

    if channel:
        embed = discord.Embed(
            title="TOURNOI DOFUS TOUCH",
            description="Clique sur participer",
            color=0x9b59b6
        )

        await channel.send(embed=embed, view=InscriptionView())


bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()