import discord
from discord import app_commands
import json
import time
from dotenv import load_dotenv
import os
from datetime import datetime

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

def init_user(user_id):
    """Initialise un utilisateur dans la DB s'il n'existe pas"""
    if user_id not in db:
        db[user_id] = {
            "tracking": False,
            "total_time": 0,
            "last_login": None,
            "is_online": False,
            "sessions": []  # Historique des sessions
        }

def format_time(seconds):
    """Formate le temps en heures/minutes lisible"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}min"

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
        await self.tree.sync()

client = MyClient()

# ====== READY ======
@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")
    
    # Initialiser les sessions en cours pour les users déjà online
    for guild in client.guilds:
        for member in guild.members:
            user_id = str(member.id)
            if user_id in db and db[user_id]["tracking"]:
                # Si l'user est online et qu'on n'a pas de last_login
                if member.status != discord.Status.offline and not db[user_id]["last_login"]:
                    db[user_id]["last_login"] = time.time()
                    db[user_id]["is_online"] = True
                    print(f"📊 Session restaurée pour {member.name}")
    
    save_db(db)

# ====== PRESENCE TRACKING ======
@client.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    user_id = str(after.id)

    # Vérifier si l'user existe et est tracké
    if user_id not in db or not db[user_id]["tracking"]:
        return

    old_status = before.status if before else discord.Status.offline
    new_status = after.status

    was_connected = old_status != discord.Status.offline
    is_connected = new_status != discord.Status.offline

    # Connexion (offline -> online)
    if not was_connected and is_connected:
        db[user_id]["last_login"] = time.time()
        db[user_id]["is_online"] = True
        save_db(db)
        print(f"🟢 {after.name} s'est connecté")

    # Déconnexion (online -> offline)
    elif was_connected and not is_connected:
        start = db[user_id]["last_login"]
        if start:
            session_duration = time.time() - start
            db[user_id]["total_time"] += session_duration
            
            # Sauvegarder l'historique de la session
            db[user_id]["sessions"].append({
                "start": start,
                "end": time.time(),
                "duration": session_duration
            })
            
            # Limiter l'historique aux 50 dernières sessions
            if len(db[user_id]["sessions"]) > 50:
                db[user_id]["sessions"] = db[user_id]["sessions"][-50:]

        db[user_id]["last_login"] = None
        db[user_id]["is_online"] = False
        save_db(db)
        print(f"🔴 {after.name} s'est déconnecté")

# ====== SLASH COMMANDS ======
@client.tree.command(name="track", description="Activer ou désactiver le suivi de temps")
@app_commands.describe(action="'on' pour activer, 'off' pour désactiver")
@app_commands.choices(action=[
    app_commands.Choice(name="Activer", value="on"),
    app_commands.Choice(name="Désactiver", value="off")
])
async def track(interaction: discord.Interaction, action: app_commands.Choice[str]):
    user_id = str(interaction.user.id)
    init_user(user_id)
    
    action_value = action.value

    if action_value == "on":
        db[user_id]["tracking"] = True
        
        # Si l'user est déjà online, démarrer le tracking immédiatement
        if interaction.user.status != discord.Status.offline:
            db[user_id]["last_login"] = time.time()
            db[user_id]["is_online"] = True
        
        msg = "✅ **Suivi activé !**\nTon temps de connexion sera maintenant enregistré."
    else:  # off
        # Si une session est en cours, la finaliser
        if db[user_id]["is_online"] and db[user_id]["last_login"]:
            session_duration = time.time() - db[user_id]["last_login"]
            db[user_id]["total_time"] += session_duration
            db[user_id]["last_login"] = None
            db[user_id]["is_online"] = False
        
        db[user_id]["tracking"] = False
        msg = "⛔ **Suivi désactivé**\nTon temps ne sera plus enregistré."
    
    save_db(db)
    await interaction.response.send_message(msg, ephemeral=True)

@client.tree.command(name="temps", description="Voir ton temps total connecté")
async def temps(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    if user_id not in db or not db[user_id]["tracking"]:
        await interaction.response.send_message(
            "❌ Aucune donnée disponible.\nUtilise `/track on` pour commencer le suivi.",
            ephemeral=True
        )
        return

    total = db[user_id]["total_time"]

    # Ajouter la session en cours si online
    current_session = 0
    if db[user_id]["is_online"] and db[user_id]["last_login"]:
        current_session = time.time() - db[user_id]["last_login"]
        total += current_session

    # Créer l'embed
    embed = discord.Embed(
        title="📊 Statistiques de connexion",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="⏱️ Temps total",
        value=format_time(total),
        inline=False
    )
    
    if db[user_id]["is_online"]:
        embed.add_field(
            name="🟢 Session actuelle",
            value=format_time(current_session),
            inline=True
        )
    
    # Nombre de sessions
    session_count = len(db[user_id].get("sessions", []))
    if db[user_id]["is_online"]:
        session_count += 1
    
    embed.add_field(
        name="🔢 Nombre de sessions",
        value=str(session_count),
        inline=True
    )
    
    embed.set_footer(text=f"Suivi actif depuis ta première connexion")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="reset", description="Réinitialiser tes statistiques de temps")
async def reset(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in db:
        await interaction.response.send_message(
            "❌ Aucune donnée à réinitialiser.",
            ephemeral=True
        )
        return
    
    # Demander confirmation
    view = ConfirmView(user_id)
    await interaction.response.send_message(
        "⚠️ **Es-tu sûr de vouloir réinitialiser toutes tes statistiques ?**\nCette action est irréversible.",
        view=view,
        ephemeral=True
    )

class ConfirmView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id

    @discord.ui.button(label="Confirmer", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ton reset !", ephemeral=True)
            return
        
        # Réinitialiser mais garder le tracking activé
        tracking_status = db[self.user_id]["tracking"]
        db[self.user_id] = {
            "tracking": tracking_status,
            "total_time": 0,
            "last_login": None,
            "is_online": False,
            "sessions": []
        }
        save_db(db)
        
        await interaction.response.edit_message(
            content="✅ **Statistiques réinitialisées avec succès !**",
            view=None
        )
        self.stop()

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ton reset !", ephemeral=True)
            return
        
        await interaction.response.edit_message(
            content="❌ Réinitialisation annulée.",
            view=None
        )
        self.stop()

# ====== LANCEMENT ======
if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if not token:
        print("❌ Erreur : TOKEN introuvable dans le fichier .env")
    else:
        client.run(token)