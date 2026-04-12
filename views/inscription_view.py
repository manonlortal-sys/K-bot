import discord


class TeamModal(discord.ui.Modal, title="Inscription équipe"):

    joueur1 = discord.ui.TextInput(label="Joueur 1", required=True)
    joueur2 = discord.ui.TextInput(label="Joueur 2", required=True)
    joueur3 = discord.ui.TextInput(label="Joueur 3", required=True)

    nom = discord.ui.TextInput(label="Nom d'équipe (optionnel)", required=False)

    async def on_submit(self, interaction: discord.Interaction):

        if len(interaction.client.teams) >= 8:
            return await interaction.response.send_message("Tournoi complet ❌", ephemeral=True)

        user_id = interaction.user.id

        is_organizer = any(role.id == 1489520344330145884 for role in interaction.user.roles)

        players = [
            self.joueur1.value.strip(),
            self.joueur2.value.strip(),
            self.joueur3.value.strip()
        ]

        # =========================
        # LOGIQUE ORGA
        # =========================
        if is_organizer:
            # orga NON inclus sauf s’il se met lui-même
            team_players = [p for p in players if str(user_id) not in p]

            # si orga se met en premier => capitaine + joueur
            if str(user_id) in self.joueur1.value:
                captain = user_id
                team_players = [user_id] + team_players
            else:
                captain = team_players[0]

        # =========================
        # JOUEUR NORMAL
        # =========================
        else:
            team_players = [user_id] + players
            captain = user_id

        team = {
            "capitaine": captain,
            "joueurs": team_players,
            "nom": self.nom.value.strip() or None
        }

        interaction.client.teams.append(team)

        await interaction.response.send_message("Équipe enregistrée ✅", ephemeral=True)

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
