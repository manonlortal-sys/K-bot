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
bot.teams_message = None

# =========================
# EMBED UPDATE (UN SEUL MESSAGE)
# =========================
async def update_teams_embed():
    channel = bot.get_channel(TEAMS_CHANNEL)

    if not channel:
        return

    embed = discord.Embed(
        title="🏆 TOURNOI - ÉQUIPES INSCRITES",
        color=0x9b59b6
    )

    if len(bot.teams) == 0:
        embed.description = "Aucune équipe pour le moment ⏳"
    else:
        for i, t in enumerate(bot.teams, 1):

            captain = f"<@{t['capitaine']}>"
            players = " • ".join([f"<@{p}>" for p in t["joueurs"]])

            embed.add_field(
                name=f"⚔️ Équipe {i}",
                value=f"👑 Capitaine : {captain}\n👥 Joueurs : {players}",
                inline=False
            )

    # SI PREMIÈRE FOIS → envoie message
    if bot.teams_message is None:
        bot.teams_message = await channel.send(embed=embed)
    else:
        await bot.teams_message.edit(embed=embed)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    channel = bot.get_channel(INSCRIPTION_CHANNEL)

    if channel:
        embed = discord.Embed(
            title="🎮 TOURNOI DOFUS TOUCH",
            description="Clique sur **Je participe** pour créer ton équipe",
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