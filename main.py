import discord
from discord.ext import commands
import threading

from config import TOKEN
from web.flask_app import app

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    print("🎮 Tournoi bot prêt")


# 🌐 Flask runner
def run_flask():
    app.run(host="0.0.0.0", port=10000)


if __name__ == "__main__":
    # Flask en thread séparé
    threading.Thread(target=run_flask).start()

    # Discord bot principal
    bot.run(TOKEN)