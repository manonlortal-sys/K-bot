import sys
import threading
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, INSCRIPTION_CHANNEL, TEAMS_CHANNEL
from web.flask_app import app
from views.inscription_view import InscriptionView

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
        self.max_teams = 8

    async def update_teams_embed(self):

        channel = await self.fetch_channel(TEAMS_CHANNEL)

        embed = discord.Embed(
            title="🏆 TOURNOI DOFUS TOUCH",
            description="Équipes inscrites",
            color=0x9b59b6
        )

        if not self.teams:
            embed.add_field(name="📭", value="Aucune équipe", inline=False)
        else:
            for i, t in enumerate(self.teams, 1):

                name = t.get("nom") or f"Équipe {i}"

                lines = []
                for idx, p in enumerate(t["joueurs"]):
                    if idx == 0:
                        lines.append(f"👑 {p} (C)")
                    else:
                        lines.append(f"👤 {p}")

                status = "⏳ En attente de paiement"
                if t.get("paid"):
                    status = "✅ Inscription payée"

                embed.add_field(
                    name=f"⚔️ {name}",
                    value="\n".join(lines) + f"\n\n💳 {status}",
                    inline=False
                )

        if self.teams_message_id is None:
            msg = await channel.send(embed=embed)
            self.teams_message_id = msg.id
        else:
            msg = await channel.fetch_message(self.teams_message_id)
            await msg.edit(embed=embed)


bot = MyBot()


@bot.event
async def on_ready():

    channel = await bot.fetch_channel(INSCRIPTION_CHANNEL)

    embed = discord.Embed(
        title="🎮 INSCRIPTION TOURNOI",
        description="Clique pour créer ton équipe",
        color=0x9b59b6
    )

    await channel.send(embed=embed, view=InscriptionView())

    await bot.update_teams_embed()


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)