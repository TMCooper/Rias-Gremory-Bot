import discord
from discord import app_commands
import json
import time
from dotenv import load_dotenv
import os

# ====== DB ======
DB_FILE = "data.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

db = load_db()
load_dotenv()

# ====== INTENTS ======
intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.guilds = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync global (peut prendre du temps)
        await self.tree.sync()

client = MyClient()

# ====== READY ======
@client.event
async def on_ready():
    print(f"Connecté en tant que {client.user}")

# ====== PRESENCE TRACKING ======
@client.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    user_id = str(after.id)

    if user_id not in db or not db[user_id]["tracking"]:
        return

    old_status = before.status if before else discord.Status.offline
    new_status = after.status

    was_connected = old_status != discord.Status.offline
    is_connected = new_status != discord.Status.offline

    # Connexion
    if not was_connected and is_connected:
        db[user_id]["last_login"] = time.time()
        db[user_id]["is_online"] = True
        save_db(db)

    # Déconnexion
    if was_connected and not is_connected:
        start = db[user_id]["last_login"]
        if start:
            session = time.time() - start
            db[user_id]["total_time"] += session

        db[user_id]["last_login"] = None
        db[user_id]["is_online"] = False
        save_db(db)

# ====== SLASH COMMANDS ======
@client.tree.command(name="track", description="Activer ou désactiver le suivi de temps")
@app_commands.describe(action="on pour activer, off pour désactiver")
async def track(interaction: discord.Interaction, action: str):
    action = action.lower()
    user_id = str(interaction.user.id)

    if action not in ("on", "off"):
        await interaction.response.send_message(
            "❌ Utilise `on` ou `off`",
            ephemeral=True
        )
        return

    if user_id not in db:
        db[user_id] = {
            "tracking": False,
            "total_time": 0,
            "last_login": None,
            "is_online": False
        }

    if action == "on":
        db[user_id]["tracking"] = True
        save_db(db)
        await interaction.response.send_message(
            "✅ Suivi activé",
            ephemeral=True
        )

    if action == "off":
        db[user_id]["tracking"] = False
        save_db(db)
        await interaction.response.send_message(
            "⛔ Suivi désactivé",
            ephemeral=True
        )

@client.tree.command(name="temps", description="Voir ton temps total connecté")
async def temps(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    if user_id not in db:
        await interaction.response.send_message(
            "Aucune donnée.",
            ephemeral=True
        )
        return

    total = db[user_id]["total_time"]

    # Ajouter session en cours si online
    if db[user_id]["is_online"] and db[user_id]["last_login"]:
        total += time.time() - db[user_id]["last_login"]

    heures = int(total // 3600)
    minutes = int((total % 3600) // 60)

    await interaction.response.send_message(
        f"🕒 Temps connecté : **{heures}h {minutes}min**",
        ephemeral=True
    )

# ====== LANCEMENT ======
client.run(os.getenv("TOKEN"))
