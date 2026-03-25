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
    """Initialise un utilisateur dans la DB s'il n'existe pas ou met à jour les champs manquants"""
    if user_id not in db:
        db[user_id] = {
            "tracking": False,
            "total_time": 0,
            "last_login": None,
            "is_online": False,
            "sessions": [],  # Historique des sessions
            "tracking_start_date": None,
            "games": {},
            "current_game": None,
            "current_game_start": None
        }
    else:
        # Migration automatique
        if "sessions" not in db[user_id]:
            db[user_id]["sessions"] = []
        if "tracking_start_date" not in db[user_id]:
            db[user_id]["tracking_start_date"] = time.time() if db[user_id].get("tracking") else None
        if "games" not in db[user_id]:
            db[user_id]["games"] = {}
        if "current_game" not in db[user_id]:
            db[user_id]["current_game"] = None
        if "current_game_start" not in db[user_id]:
            db[user_id]["current_game_start"] = None

def get_playing_game(member: discord.Member):
    """Récupère le nom du jeu auquel l'utilisateur joue actuellement"""
    for activity in member.activities:
        if activity.type == discord.ActivityType.playing:
            return activity.name
    return None

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
            if user_id in db:
                init_user(user_id)
                
            if user_id in db and db[user_id]["tracking"]:
                # Si l'user est online et qu'on n'a pas de last_login
                if member.status != discord.Status.offline and not db[user_id]["last_login"]:
                    db[user_id]["last_login"] = time.time()
                    db[user_id]["is_online"] = True
                    print(f"📊 Session restaurée pour {member.name}")
                    
                # Restaurer la session de jeu
                current_game = get_playing_game(member)
                if current_game and not db[user_id]["current_game_start"]:
                    db[user_id]["current_game"] = current_game
                    db[user_id]["current_game_start"] = time.time()
                    print(f"🎮 Session de jeu restaurée pour {member.name} ({current_game})")
    
    save_db(db)

# ====== PRESENCE TRACKING ======
@client.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    user_id = str(after.id)

    # Vérifier si l'user existe et est tracké
    if user_id not in db or not db[user_id]["tracking"]:
        return

    init_user(user_id)

    old_status = before.status if before else discord.Status.offline
    new_status = after.status

    was_connected = old_status != discord.Status.offline
    is_connected = new_status != discord.Status.offline
    
    status_changed = False

    # Connexion (offline -> online)
    if not was_connected and is_connected:
        db[user_id]["last_login"] = time.time()
        db[user_id]["is_online"] = True
        status_changed = True
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
        status_changed = True
        print(f"🔴 {after.name} s'est déconnecté")
        
    # Gestion du temps de jeu
    current_game = get_playing_game(after)
    old_game = db[user_id].get("current_game")
    
    if current_game != old_game:
        # Clôturer l'ancien jeu s'il y en avait un
        if old_game and db[user_id].get("current_game_start"):
            game_duration = time.time() - db[user_id]["current_game_start"]
            if old_game not in db[user_id]["games"]:
                db[user_id]["games"][old_game] = {"total_time": 0}
            db[user_id]["games"][old_game]["total_time"] += game_duration
            print(f"🎮 {after.name} a arrêté de jouer à {old_game} ({format_time(game_duration)})")
            
        # Lancer le nouveau jeu
        if current_game:
            db[user_id]["current_game"] = current_game
            db[user_id]["current_game_start"] = time.time()
            print(f"🎮 {after.name} a commencé à jouer à {current_game}")
        else:
            db[user_id]["current_game"] = None
            db[user_id]["current_game_start"] = None
            
        status_changed = True

    if status_changed:
        save_db(db)

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
        
        if not db[user_id].get("tracking_start_date"):
            db[user_id]["tracking_start_date"] = time.time()
        
        # Si l'user est déjà online, démarrer le tracking immédiatement
        if interaction.user.status != discord.Status.offline:
            db[user_id]["last_login"] = time.time()
            db[user_id]["is_online"] = True
            
        current_game = get_playing_game(interaction.user)
        if current_game:
            db[user_id]["current_game"] = current_game
            db[user_id]["current_game_start"] = time.time()
        
        msg = "✅ **Suivi activé !**\nTon temps de connexion et de jeu seront maintenant enregistrés."
    else:  # off
        # Si une session est en cours, la finaliser
        if db[user_id]["is_online"] and db[user_id]["last_login"]:
            session_duration = time.time() - db[user_id]["last_login"]
            db[user_id]["total_time"] += session_duration
            db[user_id]["last_login"] = None
            db[user_id]["is_online"] = False
            
        if db[user_id].get("current_game") and db[user_id].get("current_game_start"):
            game_duration = time.time() - db[user_id]["current_game_start"]
            game_name = db[user_id]["current_game"]
            if game_name not in db[user_id]["games"]:
                db[user_id]["games"][game_name] = {"total_time": 0}
            db[user_id]["games"][game_name]["total_time"] += game_duration
            db[user_id]["current_game"] = None
            db[user_id]["current_game_start"] = None
        
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
    
    start_date = db[user_id].get("tracking_start_date")
    if start_date:
        date_str = datetime.fromtimestamp(start_date).strftime("%d/%m/%Y")
        embed.set_footer(text=f"Suivi actif depuis le {date_str}")
    else:
        embed.set_footer(text="Suivi actif")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="jeux", description="Voir tes statistiques de temps de jeu")
@app_commands.describe(vue="Affichage du Top 10 ou de la Liste complète")
@app_commands.choices(vue=[
    app_commands.Choice(name="Top 10", value="top10"),
    app_commands.Choice(name="Liste complète", value="all")
])
async def jeux(interaction: discord.Interaction, vue: app_commands.Choice[str] = None):
    user_id = str(interaction.user.id)

    if user_id not in db or not db[user_id]["tracking"]:
        await interaction.response.send_message(
            "❌ Aucune donnée disponible.\nUtilise `/track on` pour commencer le suivi.",
            ephemeral=True
        )
        return

    init_user(user_id)
    
    games = db[user_id].get("games", {})
    
    # Copier les données des jeux pour pouvoir les modifier avec la session actuelle
    games_stats = {name: data["total_time"] for name, data in games.items()}
    
    # Ajouter la session en cours si l'utilisateur y joue en ce moment
    current_game = db[user_id].get("current_game")
    if current_game and db[user_id].get("current_game_start"):
        current_session = time.time() - db[user_id]["current_game_start"]
        games_stats[current_game] = games_stats.get(current_game, 0) + current_session

    if not games_stats:
        await interaction.response.send_message(
            "🎮 Tu n'as encore enregistré aucun temps de jeu.",
            ephemeral=True
        )
        return

    # Trier les jeux par temps décroissant
    sorted_games = sorted(games_stats.items(), key=lambda x: x[1], reverse=True)
    
    is_top10 = (vue is None or vue.value == "top10")
    
    if is_top10:
        sorted_games = sorted_games[:10]
        title = "🎮 Top 10 des jeux joués"
    else:
        title = "🎮 Liste complète des jeux joués"

    embed = discord.Embed(
        title=title,
        color=discord.Color.green()
    )
    
    # Discord Embed fields limit is 25.
    if len(sorted_games) > 25:
        sorted_games = sorted_games[:25]
        embed.description = "*(Limité aux 25 premiers pour l'affichage)*"

    for i, (game_name, total_sec) in enumerate(sorted_games, 1):
        medal = ""
        if i == 1: medal = "🥇 "
        elif i == 2: medal = "🥈 "
        elif i == 3: medal = "🥉 "
        else: medal = f"`#{i}` "
        
        status = " *(En cours)*" if game_name == current_game else ""
        
        embed.add_field(
            name=f"{medal}{game_name}",
            value=f"⏱️ {format_time(total_sec)}{status}",
            inline=False
        )
    
    start_date = db[user_id].get("tracking_start_date")
    if start_date:
        date_str = datetime.fromtimestamp(start_date).strftime("%d/%m/%Y")
        embed.set_footer(text=f"Suivi actif depuis le {date_str} • {len(games_stats)} jeux au total")
    else:
        embed.set_footer(text=f"Suivi actif • {len(games_stats)} jeux au total")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="reset", description="Réinitialiser tes statistiques de temps et de jeux")
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
        
        # Réinitialiser mais garder le tracking activé et la date de début
        tracking_status = db[self.user_id]["tracking"]
        start_date = db[self.user_id].get("tracking_start_date")
        
        db[self.user_id] = {
            "tracking": tracking_status,
            "total_time": 0,
            "last_login": None,
            "is_online": False,
            "sessions": [],
            "tracking_start_date": start_date,
            "games": {},
            "current_game": None,
            "current_game_start": None
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