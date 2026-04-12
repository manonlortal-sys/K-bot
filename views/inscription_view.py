import discord

class InscriptionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Je participe", style=discord.ButtonStyle.green)
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Tu es inscrit ! (phase 1 OK)",
            ephemeral=True
        )