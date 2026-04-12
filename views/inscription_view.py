import discord


class InscriptionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Je participe",
        style=discord.ButtonStyle.success,
        custom_id="tournoi:participate"
    )
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):

        if len(interaction.client.teams) >= 8:
            return await interaction.response.send_message(
                "Tournoi complet ❌",
                ephemeral=True
            )

        await interaction.response.send_message(
            "Envoie dans cet ordre :\n1️⃣ Nom d’équipe\n2️⃣ Joueurs (séparés par espace)",
            ephemeral=True
        )

        def check(msg):
            return msg.author.id == interaction.user.id

        msg = await interaction.client.wait_for("message", timeout=120, check=check)

        parts = msg.content.split()

        if len(parts) < 3:
            return await interaction.followup.send(
                "Format invalide ❌ (nom + au moins 2 joueurs)",
                ephemeral=True
            )

        team_name = parts[0]
        players = parts[1:3]

        team = {
            "capitaine": interaction.user.id,
            "joueurs": [interaction.user.id] + players,
            "nom": team_name
        }

        interaction.client.teams.append(team)

        await interaction.followup.send("Équipe enregistrée ✅", ephemeral=True)

        await interaction.client.update_teams_embed()