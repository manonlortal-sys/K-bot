import discord
from discord.ext import commands


class TeamsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def update_teams_embed(self):

        channel = await self.bot.fetch_channel(self.bot.TEAMS_CHANNEL)

        embed = discord.Embed(
            title="🏆 TOURNOI DOFUS TOUCH",
            color=0x9b59b6
        )

        for i, t in enumerate(self.bot.teams, 1):

            name = t.get("nom") or f"Équipe {i}"

            players = []
            for p in t["joueurs"]:
                players.append(f"👤 {p}")

            status = "⏳ En attente de paiement"
            if t.get("paid"):
                status = "✅ Inscription payée"

            embed.add_field(
                name=f"⚔️ {name}",
                value="\n".join(players) + f"\n\n💳 {status}",
                inline=False
            )

        if self.bot.teams_message_id is None:
            msg = await channel.send(embed=embed)
            self.bot.teams_message_id = msg.id
        else:
            msg = await channel.fetch_message(self.bot.teams_message_id)
            await msg.edit(embed=embed)


async def setup(bot):
    await bot.add_cog(TeamsCog(bot))