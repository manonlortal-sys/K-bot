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

        # ORGANISATEUR
        if is_organizer:
            players = parts[:3]  # 3 joueurs max fournis

            # IMPORTANT : on retire l’organisateur s’il apparaît dans la liste
            players = [p for p in players if str(user_id) not in p]

            team = {
                "capitaine": players[0] if len(players) > 0 else user_id,
                "joueurs": players
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