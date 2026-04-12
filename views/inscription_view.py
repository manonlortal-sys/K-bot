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
            return await interaction.response.send_message(
                "❌ Les inscriptions sont fermées.",
                ephemeral=True
            )

        # création équipe temporaire (step 1)
        team = {
            "id": str(user.id),
            "name": None,
            "captain_id": user.id,
            "players": [user.id]
        }

        tournament["teams"].append(team)

        await interaction.response.send_message(
            "👥 Donne maintenant les joueurs de ton équipe (format libre).\n"
            "Ex: @user1 @user2 ou pseudos séparés",
            ephemeral=True
        )
