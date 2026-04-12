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

        await interaction.response.send_message(
            "Envoie les joueurs de ton équipe (séparés par espace)",
            ephemeral=True
        )

        def check(msg):
            return msg.author.id == interaction.user.id

        msg = await interaction.client.wait_for("message", timeout=120, check=check)

        parts = msg.content.split()

        if len(parts) < 2:
            return await interaction.followup.send("Minimum 2 joueurs ❌", ephemeral=True)

        user_id = interaction.user.id

        is_organizer = any(role.id == 1489520344330145884 for role in interaction.user.roles)

        # LIMIT 8 TEAMS
        if len(interaction.client.teams) >= 8:
            return await interaction.followup.send("Tournoi complet ❌", ephemeral=True)

        # ORGANISATEUR
        if is_organizer:
            team = {
                "capitaine": parts[0],
                "joueurs": parts[:3]
            }

        # JOUEUR NORMAL
        else:
            team = {
                "capitaine": user_id,
                "joueurs": [user_id] + parts[:2]
            }

        interaction.client.teams.append(team)

        await interaction.followup.send("Équipe enregistrée ✅", ephemeral=True)

        await interaction.client.update_teams_embed()