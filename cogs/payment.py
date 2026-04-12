import discord
from discord.ext import commands


class PaymentView(discord.ui.View):

    def __init__(self, team):
        super().__init__(timeout=None)
        self.team = team

    @discord.ui.button(label="Payé ✅", style=discord.ButtonStyle.success)
    async def paid(self, interaction, button):

        role_id = 1489520344330145884

        if role_id not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ réservé aux organisateurs", ephemeral=True)

        self.team["paid"] = True

        await interaction.response.send_message("✅ Paiement validé", ephemeral=True)

        teams_cog = interaction.client.get_cog("TeamsCog")
        if teams_cog:
            await teams_cog.update_teams_embed()


class PaymentCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def send_payment_message(self, team, channel):

        embed = discord.Embed(
            title="🏆 Inscription finalisée",
            color=0x9b59b6
        )

        embed.add_field(name="🏷 Équipe", value=team["nom"] or "Équipe auto", inline=False)
        embed.add_field(name="👥 Joueurs", value="\n".join(team["joueurs"]), inline=False)
        embed.add_field(name="💳 Statut", value="⏳ En attente de paiement", inline=False)

        view = PaymentView(team)

        await channel.send(
            content="<@&1489520344330145884>",
            embed=embed,
            view=view
        )


async def setup(bot):
    await bot.add_cog(PaymentCog(bot))