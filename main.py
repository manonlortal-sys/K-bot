import sys
import threading
import discord
from discord.ext import commands

from config import DISCORD_TOKEN
from web.flask_app import app

# =========================
# AUDIOOP FIX (Render)
# =========================
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop
    sys.modules["audioop"] = audioop


def run_flask():
    app.run(host="0.0.0.0", port=10000)


class MyBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)

        self.teams = []
        self.teams_message_id = None


bot = MyBot()


async def setup():
    await bot.load_extension("cogs.registration")
    await bot.load_extension("cogs.teams")
    await bot.load_extension("cogs.payment")
    await bot.load_extension("cogs.tournament")
    print("✅ Cogs chargés")


@bot.event
async def on_ready():
    print(f"BOT CONNECTÉ : {bot.user}")


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.loop.create_task(setup())
    bot.run(DISCORD_TOKEN)