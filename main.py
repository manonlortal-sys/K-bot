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
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

        self.teams = []
        self.teams_message_id = None
        self.max_teams = 8

    async def update_teams_embed(self):
        channel = await self.fetch_channel(TEAMS_CHANNEL)

        embed = discord.Embed(
            title="🏆 TOURNOI - ÉQUIPES",
            color=0x9b59b6
        )

        if len(self.teams) == 0:
            embed.description = "Aucune équipe pour le moment ⏳"
        else:
            for i, t in enumerate(self.teams, 1):

                # CLEAN DISPLAY (ANTI @@ + PAS DE < > BRUT)
                captain = f"<@{t['capitaine']}>"

                players = []
                for p in t["joueurs"]:
                    players.append(f"<@{p}>")

                players_text = " • ".join(players)

                embed.add_field(
                    name=f"⚔️ Équipe {i}",
                    value=f"👑 Capitaine : {captain}\n👥 Joueurs : {players_text}",
                    inline=False
                )

        if self.teams_message_id is None:
            msg = await channel.send(embed=embed)
            self.teams_message_id = msg.id
        else:
            msg = await channel.fetch_message(self.teams_message_id)
            await msg.edit(embed=embed)

bot = MyBot()

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print("BOT READY")

    channel = await bot.fetch_channel(INSCRIPTION_CHANNEL)

    embed = discord.Embed(
        title="🎮 TOURNOI DOFUS TOUCH",
        description="Clique sur Je participe pour créer une équipe",
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