import discord


class InscriptionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Je participe",
        style=discord.ButtonStyle.green,
        custom_id="tournoi:participate"
    )
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "Envoie les 2 joueurs de ton équipe (mention @ ou pseudo, séparés par espace)",
            ephemeral=True
        )

        def check(msg):
            return msg.author.id == interaction.user.id

        try:
            msg = await interaction.client.wait_for("message", timeout=120, check=check)
        except:
            return await interaction.followup.send("Temps écoulé ❌", ephemeral=True)

        parts = msg.content.split()

        if len(parts) < 2:
            return await interaction.followup.send(
                "Tu dois fournir 2 joueurs minimum ❌",
                ephemeral=True
            )

        team = {
            "capitaine": interaction.user.id,
            "joueurs": [interaction.user.id],
            "raw_players": parts[:2],
            "nom": None,
            "validated": False
        }

        interaction.client.teams.append(team)

        await interaction.followup.send(
            "Équipe enregistrée ✅\nAttends validation des organisateurs.",
            ephemeral=True
        )