import discord
from discord.ext import commands


class TeamsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.update_teams_embed()

    async def update_teams_embed(self):

        channel = await self.bot.fetch_channel(self.bot.TEAMS_CHANNEL)

        embed = discord.Embed(
            title="🏆 TOURNOI DOFUS TOUCH",
            color=0x9b59b6
        )

        if not self.bot.teams:
            embed.add_field(name="📭", value="Aucune équipe", inline=False)
        else:
            for i, t in enumerate(self.bot.teams, 1):

                name = t.get("nom") or f"Équipe {i}"

                players = []
                for idx, p in enumerate(t["joueurs"]):
                    if idx == 0:
                        players.append(f"👤 {p} (C)")
                    else:
                        players.append(f"👤 {p}")

                status = "⏳ En attente de paiement"
                if t.get("paid"):
                    status = "✅ Inscription payée"

                embed.add_field(
                    name=f"⚔️ {name}",
                    value="\n".join(players) + f"\n💳 {status}\n",
                    inline=False
                )

        if self.bot.teams_message_id is None:
            msg = await channel.send(embed=embed)
            self.bot.teams_message_id = msg.id
        else:
            msg = await channel.fetch_message(self.bot.teams_message_id)
            await msg.edit(embed=embed)

        # 🔥 fermeture auto
        if len(self.bot.teams) == 8:
            cog = self.bot.get_cog("TournamentCog")
            if cog and not cog.closed:
                await cog.close_registration()