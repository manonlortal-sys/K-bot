import discord
from discord.ui import View, button

from core.state import tournament
from utils.validators import parse_players
from services.team_service import create_team

class InscriptionView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @button(label="🎮 Je participe", style=discord.ButtonStyle.green)
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user

        if tournament["phase"] != "signup":
            return await interaction.response.send_message("❌ Fermé.", ephemeral=True)

        for team in tournament["teams"]:
            if team["captain_id"] == user.id:
                return await interaction.response.send_message("❌ Déjà une équipe.", ephemeral=True)

        await interaction.response.send_message(
            "👥 Envoie les joueurs (mentions ou pseudos, max 2).",
            ephemeral=True
        )

        def check(m):
            return m.author.id == user.id

        msg = await interaction.client.wait_for("message", check=check)

        players = parse_players(msg.content)

        team = create_team(user.id, players)

        await interaction.followup.send("✅ Équipe créée.")