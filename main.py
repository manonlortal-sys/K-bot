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

        if not self.teams:
            embed.description = "Aucune équipe"
        else:
            for i, t in enumerate(self.teams, 1):

                captain_id = t["capitaine"]
                players = t["joueurs"]

                # affichage propre sans <> ni double @
                formatted_players = []

                for idx, p in enumerate(players):
                    if idx == 0:
                        formatted_players.append(f"(C) <@{p}>")
                    else:
                        formatted_players.append(f"<@{p}>")

                players_text = ", ".join(formatted_players)

                name = t.get("nom") or f"Équipe {i}"

                embed.add_field(
                    name=f"⚔️ {name}",
                    value=players_text,
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
        description="Clique pour t'inscrire",
        color=0x9b59b6
    )

    await channel.send(embed=embed, view=InscriptionView())

    await bot.update_teams_embed()


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)
