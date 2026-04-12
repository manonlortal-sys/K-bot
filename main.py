import sys
import threading
import discord
from discord.ext import commands

from config import (
    DISCORD_TOKEN,
    INSCRIPTION_CHANNEL,
    TEAMS_CHANNEL,
    ROLE_ORGA
)

from web.flask_app import app
from views.inscription_view import InscriptionView

# =========================
# AUDIOOP FIX (Python 3.13)
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
# UPDATE EMBED TEAMS
# =========================
async def update_teams_embed():
    channel = bot.get_channel(TEAMS_CHANNEL)
    if not channel:
        return

    embed = discord.Embed(
        title="ÉQUIPES INSCRITES",
        color=0x9b59b6
    )

    if not bot.teams:
        embed.description = "Aucune équipe pour le moment."
    else:
        for i, t in enumerate(bot.teams, 1):
            status = "✅ Validée" if t["validated"] else "⏳ En attente"
            embed.add_field(
                name=f"Équipe {i}",
                value=f"{status}\nCapitaine: <@{t['capitaine']}>",
                inline=False
            )

    await channel.purge(limit=10)
    await channel.send(embed=embed)

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

# =========================
# VALIDATION COMMANDE
# =========================
@bot.command()
async def valider(ctx, index: int):
    if ROLE_ORGA not in [r.id for r in ctx.author.roles]:
        return await ctx.send("❌ Pas autorisé")

    if index < 1 or index > len(bot.teams):
        return await ctx.send("❌ Index invalide")

    bot.teams[index - 1]["validated"] = True

    await ctx.send(f"Équipe {index} validée ✅")

    await update_teams_embed()

# =========================
# START
# =========================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)