import sys
import threading
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, INSCRIPTION_CHANNEL, TEAMS_CHANNEL
from web.flask_app import app

# =========================
# FIX AUDIOOP
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

        # IMPORTANT
        self.INSCRIPTION_CHANNEL = INSCRIPTION_CHANNEL
        self.TEAMS_CHANNEL = TEAMS_CHANNEL

    async def setup_hook(self):
        await self.load_extension("cogs.registration")
        await self.load_extension("cogs.teams")
        await self.load_extension("cogs.payment")
        await self.load_extension("cogs.tournament")

        print("✅ Cogs chargés")

    async def on_ready(self):
        print(f"BOT CONNECTÉ : {self.user}")


bot = MyBot()


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)