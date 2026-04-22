import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import uuid
import datetime
from flask import Flask, request, jsonify
import threading
import sys
from ultralytics import YOLO

# ==========================================================
# 🛠️ KONFIGURIMI I RRUGËS (FIX PËR FOLDERIN _INTERNAL)
# ==========================================================
def get_base_path():
    """Gjen folderin ku ndodhet modeli, duke kontrolluar edhe folderin _internal"""
    if getattr(sys, 'frozen', False):
        # Rruga ku ndodhet EXE-ja
        exe_dir = os.path.dirname(sys.executable)
        # Rruga e folderit _internal
        internal_path = os.path.join(exe_dir, "_internal")
        
        # Nëse modeli është brenda _internal, përdor atë rrugë
        if os.path.exists(os.path.join(internal_path, "yolov8n.pt")):
            return internal_path
        return exe_dir
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")
# Keys.json ruhet gjithmonë te folderi kryesor i EXE për akses më të lehtë
KEYS_FILE = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else BASE_DIR, "keys.json")

# ==========================================================
# ⚙️ KONFIGURIMI I SISTEMIT DHE BOTIT
# ==========================================================
TOKEN = os.environ.get('DISCORD_TOKEN') 
OWNER_ID = 1386797649532948570 
file_lock = threading.Lock()

class XrayBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"✅ Slash commands synchronized: {len(synced)} commands.")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

bot = XrayBot()

# --- FUNKSIONET E DATABAZËS (JSON) ---
def load_keys():
    with file_lock:
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r") as f:
                    content = f.read()
                    return json.loads(content) if content else {}
            except:
                return {}
        return {}

def save_keys(keys):
    with file_lock:
        with open(KEYS_FILE, "w") as f:
            json.dump(keys, f, indent=4)

# ==========================================================
# 🌐 SERVERI AUTH DHE UPDATE (FLASK API)
# ==========================================================
app = Flask('')

@app.route('/')
def home():
    return "XrayGamer Global Auth Server is Online."

@app.route('/check_update', methods=['GET'])
def check_update():
    return jsonify({
        "version": "1.0.0",
        "url": "https://drive.google.com/file/d/1b4-7trPriu49TMET8Si-oucpDUUJDXPQ/view?usp=sharing"
    })

@app.route('/check_key', methods=['GET'])
def check_key():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    
    if not key or not hwid:
        return jsonify({"status": "error", "message": "Missing parameters!"}), 400
    
    keys = load_keys()
    
    if key in keys:
        if keys[key].get("status") == "disabled":
            return jsonify({"status": "error", "message": "License Blocked by Admin!"}), 403

        expires_at = keys[key].get("expires_at", "never")
        if expires_at != "never":
            expiry_date = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() > expiry_date:
                return jsonify({"status": "error", "message": "License Expired!"}), 403

        if keys[key]['hwid'] is None:
            keys[key]['hwid'] = hwid
            save_keys(keys)
            return jsonify({"status": "success", "message": "Hardware Bound Successfully!"})
        
        if keys[key]['hwid'] == hwid:
            return jsonify({"status": "success", "message": "Access Granted!"})
        else:
            return jsonify({"status": "error", "message": "HWID Mismatch!"}), 401
            
    return jsonify({"status": "error", "message": "Invalid License Key!"}), 404

# ==========================================================
# 🤖 NGARKIMI I AI ENGINE (FIX PËR _INTERNAL)
# ==========================================================
def initialize_ai():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Loading AI Engine (YOLOv8)...")
    print(f"[*] Searching model at: {MODEL_PATH}")
    
    if os.path.exists(MODEL_PATH):
        try:
            # Ngarkojmë modelin direkt nga rruga e gjetur (lokale)
            model = YOLO(MODEL_PATH)
            print(f"✅ AI Engine Loaded successfully from local file!")
            return model
        except Exception as e:
            print(f"❌ CRITICAL AI ERROR: {e}")
            return None
    else:
        print(f"❌ CRITICAL AI ERROR: {MODEL_PATH} NOT FOUND!")
        return None

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================================
# 💬 KOMANDAT E DISCORD (SLASH COMMANDS)
# ==========================================================

@bot.tree.command(name="getkey", description="Generate your unique 2-hour Trial key")
async def getkey(interaction: discord.Interaction):
    local_keys = load_keys()
    for k, v in local_keys.items():
        if v.get("user_id") == interaction.user.id:
            return await interaction.response.send_message(f"⚠️ You already have a key: `{k}`", ephemeral=True)

    new_key = f"XRAY-{str(uuid.uuid4())[:8].upper()}"
    expiry_time = (datetime.datetime.now() + datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")

    local_keys[new_key] = {
        "user": str(interaction.user),
        "user_id": interaction.user.id,
        "hwid": None,
        "status": "active",
        "expires_at": expiry_time
    }
    save_keys(local_keys)
    
    embed = discord.Embed(title="🚀 XrayGamer Trial Activated", color=discord.Color.green())
    embed.add_field(name="Your License Key", value=f"```\n{new_key}\n```", inline=False)
    embed.set_footer(text="Buy Lifetime at xraygamer.sell.app")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="links", description="Show official project links")
async def links(interaction: discord.Interaction):
    embed = discord.Embed(title="🔗 XrayGamer Official Links", color=discord.Color.blue())
    embed.add_field(name="📁 GitHub", value="[Project Hub](https://github.com/XrayGamerOfficial97/XrayGamer-Project-Hub)", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="admin_add_vip", description="Add a Lifetime VIP Key (Admin Only)")
async def admin_add_vip(interaction: discord.Interaction, key_name: str):
    if interaction.user.id != OWNER_ID: return
    local_keys = load_keys()
    local_keys[key_name] = {"user": "VIP_LIFETIME", "user_id": None, "hwid": None, "status": "active", "expires_at": "never"}
    save_keys(local_keys)
    await interaction.response.send_message(f"✅ VIP Key `{key_name}` added.", ephemeral=True)

@bot.tree.command(name="admin_keys", description="View all keys (Admin Only)")
async def admin_keys(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID: return
    keys = load_keys()
    if not keys: return await interaction.response.send_message("Empty.", ephemeral=True)
    msg = "### 🔑 LICENSE LIST\n"
    for k, v in keys.items():
        msg += f"**{k}** | HWID: `{v['hwid']}`\n"
    await interaction.response.send_message(msg[:2000], ephemeral=True)

@bot.tree.command(name="admin_reset_key", description="Reset HWID (Admin Only)")
async def admin_reset_key(interaction: discord.Interaction, key_name: str):
    if interaction.user.id != OWNER_ID: return
    local_keys = load_keys()
    if key_name in local_keys:
        local_keys[key_name]['hwid'] = None
        save_keys(local_keys)
        await interaction.response.send_message(f"🔄 Reset `{key_name}`.", ephemeral=True)

# ==========================================================
# 🚀 NISJA
# ==========================================================
@bot.event
async def on_ready():
    print(f'🚀 XrayGamer Bot Online: {bot.user}')

if __name__ == "__main__":
    # 1. Ngarko AI (Tani kontrollon _internal automatikisht)
    ai_instance = initialize_ai()
    
    # 2. Nis API
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 3. Nis Botin
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: DISCORD_TOKEN missing!")
