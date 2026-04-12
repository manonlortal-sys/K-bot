import discord
import random
from discord.ext import commands


class TournamentCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.closed = False

    async def close_registration(self):

        self.closed = True

        channel = await self.bot.fetch_channel(1492796809351925831)

        embed = discord.Embed(
            title="🚨 Inscriptions clôturées",
            description="Merci d’attribuer le rôle participant à tous les joueurs",
            color=0xff0000
        )

        view = TournamentView(self)

        await channel.send(
            content="<@&1489520344330145884>",
            embed=embed,
            view=view
        )

    def generate_bracket(self):

        teams = self.bot.teams[:]
        random.shuffle(teams)

        return [(teams[i], teams[i+1]) for i in range(0, 8, 2)]


class TournamentView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="🎲 Lancer le tirage", style=discord.ButtonStyle.primary)
    async def draw(self, interaction, button):

        role_id = 1489520344330145884

        if role_id not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ réservé aux organisateurs", ephemeral=True)

        bracket = self.cog.generate_bracket()

        embed = discord.Embed(
            title="🎲 Tirage des matchs",
            color=0x9b59b6
        )

        for i, (a, b) in enumerate(bracket, 1):

            embed.add_field(
                name=f"🔥 MATCH {i}",
                value=f"{a['nom'] or 'Équipe'}\nVS\n{b['nom'] or 'Équipe'}",
                inline=False
            )

        channel = await interaction.client.fetch_channel(interaction.client.TEAMS_CHANNEL)

        await channel.send(embed=embed)

        await interaction.response.send_message("✅ Tirage effectué", ephemeral=True)


async def setup(bot):
    await bot.add_cog(TournamentCog(bot))