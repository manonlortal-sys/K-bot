import discord


class TeamModal(discord.ui.Modal, title="Inscription équipe"):

    joueur1 = discord.ui.TextInput(label="Joueur 1", required=True)
    joueur2 = discord.ui.TextInput(label="Joueur 2", required=True)
    joueur3 = discord.ui.TextInput(label="Joueur 3", required=True)

    nom = discord.ui.TextInput(
        label="Nom d'équipe (optionnel)",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):

        if len(interaction.client.teams) >= 8:
            return await interaction.response.send_message(
                "Tournoi complet ❌",
                ephemeral=True
            )

        team_name = self.nom.value.strip() or None

        team = {
            "capitaine": interaction.user.id,
            "joueurs": [
                interaction.user.id,
                self.joueur1.value,
                self.joueur2.value,
                self.joueur3.value
            ],
            "nom": team_name
        }

        interaction.client.teams.append(team)

        await interaction.response.send_message(
            "Équipe enregistrée ✅",
            ephemeral=True
        )

        await interaction.client.update_teams_embed()


class InscriptionView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Je participe",
        style=discord.ButtonStyle.success,
        custom_id="tournoi:participate"
    )
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(TeamModal())