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
bot.teams_message_id = None

# =========================
# EMBED UPDATE (SAFE)
# =========================
async def update_teams_embed():
    channel = await bot.fetch_channel(TEAMS_CHANNEL)

    embed = discord.Embed(
        title="🏆 TOURNOI - ÉQUIPES INSCRITES",
        color=0x9b59b6
    )

    if len(bot.teams) == 0:
        embed.description = "Aucune équipe pour le moment ⏳"
    else:
        for i, t in enumerate(bot.teams, 1):
            players = " • ".join([f"<@{p}>" for p in t["joueurs"]])

            embed.add_field(
                name=f"⚔️ Équipe {i}",
                value=f"👑 <@{t['capitaine']}>\n👥 {players}",
                inline=False
            )

    # PREMIÈRE FOIS → créer message
    if bot.teams_message_id is None:
        msg = await channel.send(embed=embed)
        bot.teams_message_id = msg.id
    else:
        msg = await channel.fetch_message(bot.teams_message_id)
        await msg.edit(embed=embed)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print("Bot ready")

    channel = await bot.fetch_channel(INSCRIPTION_CHANNEL)

    embed = discord.Embed(
        title="🎮 TOURNOI DOFUS TOUCH",
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