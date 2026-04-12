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

        # =========================
        # ETAPE 1 : JOUEURS
        # =========================
        await interaction.response.send_message(
            "Envoie les 3 joueurs de ton équipe (séparés par espace)",
            ephemeral=True
        )

        def check(msg):
            return msg.author.id == interaction.user.id

        msg = await interaction.client.wait_for("message", timeout=120, check=check)

        parts = msg.content.split()

        if len(parts) < 3:
            return await interaction.followup.send(
                "❌ Il faut exactement 3 joueurs",
                ephemeral=True
            )

        players = parts[:3]

        # =========================
        # ETAPE 2 : NOM ÉQUIPE
        # =========================
        await interaction.followup.send(
            "Donne un nom d’équipe (ou écris `skip` pour nom automatique)",
            ephemeral=True
        )

        msg2 = await interaction.client.wait_for("message", timeout=120, check=check)

        if msg2.content.lower() == "skip":
            team_name = None
        else:
            team_name = msg2.content.strip()

        # =========================
        # CREATION TEAM
        # =========================
        team = {
            "capitaine": interaction.user.id,
            "joueurs": [interaction.user.id] + players,
            "nom": team_name
        }

        interaction.client.teams.append(team)

        await interaction.followup.send("Équipe enregistrée ✅", ephemeral=True)

        await interaction.client.update_teams_embed()