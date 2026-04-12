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
            "Envoie les 2 joueurs de ton équipe",
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
            return await interaction.followup.send("2 joueurs minimum ❌", ephemeral=True)

        team = {
            "capitaine": interaction.user.id,
            "joueurs": parts[:2],
            "validated": False
        }

        interaction.client.teams.append(team)

        await interaction.followup.send(
            "Équipe enregistrée ✅ (en attente validation)",
            ephemeral=True
        )

        # update embed live
        await interaction.client.loop.create_task(
            update_teams(interaction.client)
        )


async def update_teams(client):
    from main import update_teams_embed
    await update_teams_embed()