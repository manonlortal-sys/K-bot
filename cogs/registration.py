import discord
from discord.ext import commands


class RegistrationView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.sessions = {}

    @discord.ui.button(label="🎮 Je participe", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.sessions[interaction.user.id] = {"joueurs": None, "nom": None}

        await interaction.response.send_message(
            "👥 Envoie les 3 joueurs ici",
            ephemeral=True
        )

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        msg = await interaction.client.wait_for("message", check=check)

        self.sessions[interaction.user.id]["joueurs"] = msg.content.split()[:3]

        await self.ask_name(interaction)

    async def ask_name(self, interaction):

        view = NameView(self)
        await interaction.followup.send(
            "🏷 Nom d’équipe ou passer",
            view=view,
            ephemeral=True
        )

    async def recap(self, interaction, uid):

        s = self.sessions[uid]

        embed = discord.Embed(
            title="📋 Récap équipe",
            description="\n".join([f"👤 {p}" for p in s["joueurs"]]),
            color=0x9b59b6
        )

        embed.add_field(name="🏷 Nom", value=s["nom"] or "Équipe auto")

        view = ConfirmView(self, uid)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class NameView(discord.ui.View):

    def __init__(self, parent):
        super().__init__(timeout=60)
        self.parent = parent

    @discord.ui.button(label="⏭ Passer", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction, button):

        await interaction.response.defer()
        self.parent.sessions[interaction.user.id]["nom"] = None
        await self.parent.recap(interaction, interaction.user.id)

    @discord.ui.button(label="🏷 Inscrire nom", style=discord.ButtonStyle.primary)
    async def set_name(self, interaction, button):

        await interaction.response.send_message("Envoie le nom", ephemeral=True)

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        msg = await interaction.client.wait_for("message", check=check)

        self.parent.sessions[interaction.user.id]["nom"] = msg.content
        await self.parent.recap(interaction, interaction.user.id)


class ConfirmView(discord.ui.View):

    def __init__(self, parent, uid):
        super().__init__()
        self.parent = parent
        self.uid = uid

    @discord.ui.button(label="🟢 Valider", style=discord.ButtonStyle.success)
    async def validate(self, interaction, button):

        session = self.parent.sessions[self.uid]

        team = {
            "joueurs": session["joueurs"],
            "nom": session["nom"],
            "paid": False
        }

        interaction.client.teams.append(team)

        del self.parent.sessions[self.uid]

        await interaction.response.send_message("✅ OK", ephemeral=True)

        await self.cog.update_teams_embed()


class RegistrationCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):

        channel = await self.bot.fetch_channel(self.bot.INSCRIPTION_CHANNEL)

        embed = discord.Embed(
            title="🎮 INSCRIPTION TOURNOI",
            color=0x9b59b6
        )

        await channel.send(embed=embed, view=RegistrationView(self))


async def setup(bot):
    await bot.add_cog(RegistrationCog(bot))