import discord
from discord.ext import commands


class PaymentView(discord.ui.View):

    def __init__(self, team):
        super().__init__()
        self.team = team

    @discord.ui.button(label="Payé ✅", style=discord.ButtonStyle.success)
    async def paid(self, interaction, button):

        role_id = 1489520344330145884

        if role_id not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ orga only", ephemeral=True)

        self.team["paid"] = True

        await interaction.response.send_message("✅ payé", ephemeral=True)

        await interaction.client.get_cog("TeamsCog").update_teams_embed()


class PaymentCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def send_payment_message(self, team, channel):

        embed = discord.Embed(
            title="🏆 Inscription finalisée",
            color=0x9b59b6
        )

        embed.add_field(name="👥 Joueurs", value="\n".join(team["joueurs"]))
        embed.add_field(name="💳 Statut", value="⏳ En attente de paiement")

        view = PaymentView(team)

        await channel.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PaymentCog(bot))