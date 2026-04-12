import discord
from discord.ui import View, button
from core.state import tournament

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

        team = {
            "id": str(user.id),
            "name": None,
            "captain_id": user.id,
            "players": [user.id]
        }

        tournament["teams"].append(team)

        await interaction.response.send_message("👥 Équipe créée.", ephemeral=True)