import discord
import random
from discord.ext import commands


class TournamentCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.closed = False

    async def close_registration(self):

        channel = await self.bot.fetch_channel(self.bot.TEAMS_CHANNEL)

        embed = discord.Embed(
            title="🚨 INSCRIPTIONS CLÔTURÉES",
            description="8 équipes atteintes",
            color=0xff0000
        )

        view = TournamentView(self)

        await channel.send(embed=embed, view=view)

    def generate_bracket(self):

        teams = self.bot.teams[:]
        random.shuffle(teams)

        return [
            (teams[0], teams[1]),
            (teams[2], teams[3]),
            (teams[4], teams[5]),
            (teams[6], teams[7])
        ]


class TournamentView(discord.ui.View):

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    @discord.ui.button(label="🎲 Lancer le tirage", style=discord.ButtonStyle.primary)
    async def draw(self, interaction, button):

        role_id = 1489520344330145884

        if role_id not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ orga only", ephemeral=True)

        bracket = self.cog.generate_bracket()

        embed = discord.Embed(
            title="🎲 MATCHS",
            color=0x9b59b6
        )

        for i, (a, b) in enumerate(bracket, 1):

            embed.add_field(
                name=f"🔥 MATCH {i}",
                value=f"{a['nom'] or 'Team'}\nVS\n{b['nom'] or 'Team'}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(TournamentCog(bot))