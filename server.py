import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import uuid
import datetime
from flask import Flask, request, jsonify
import threading

# --- KONFIGURIMI I SISTEMIT ---
TOKEN = os.environ.get('DISCORD_TOKEN')
OWNER_ID = 1386797649532948570
KEYS_FILE = "keys.json"
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

# ================= SERVERI AUTH (FLASK API) =================
# Ky server shërben për të vërtetuar licencën kur hapet programi .EXE
app = Flask('')

@app.route('/')
def home():
    return "XrayGamer Global Auth Server is Online."

@app.route('/check_key', methods=['GET'])
def check_key():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    
    if not key or not hwid:
        return jsonify({"status": "error", "message": "Missing parameters!"}), 400
    
    keys = load_keys()
    
    if key in keys:
        # Kontrolli i Statusit (Nëse është i bllokuar nga Admini)
        if keys[key].get("status") == "disabled":
            return jsonify({"status": "error", "message": "License Blocked by Admin!"}), 403

        # 1. Kontrolli i Skadimit (Trial Check)
        expires_at = keys[key].get("expires_at", "never")
        if expires_at != "never":
            expiry_date = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() > expiry_date:
                return jsonify({"status": "error", "message": "License Expired!"}), 403

        # 2. Kontrolli i HWID (Hardware Lock)
        if keys[key]['hwid'] is None:
            keys[key]['hwid'] = hwid
            save_keys(keys)
            return jsonify({"status": "success", "message": "Hardware Bound Successfully!"})
        
        if keys[key]['hwid'] == hwid:
            return jsonify({"status": "success", "message": "Access Granted!"})
        else:
            return jsonify({"status": "error", "message": "HWID Mismatch! Key used on another PC."}), 401
            
    return jsonify({"status": "error", "message": "Invalid License Key!"}), 404

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= KOMANDAT E DISCORD (SLASH) =================

@bot.tree.command(name="getkey", description="Generate your unique 2-hour Trial key")
async def getkey(interaction: discord.Interaction):
    local_keys = load_keys()
    
    # Mbrojtja: Mos lejo të marrin më shumë se 1 çelës për llogari
    for k, v in local_keys.items():
        if v.get("user_id") == interaction.user.id:
            return await interaction.response.send_message(f"⚠️ You already have a key linked to this account: `{k}`", ephemeral=True)

    # Gjenerimi i çelësit Trial (2 orë)
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
    embed.add_field(name="Duration", value="2 Hours", inline=True)
    embed.add_field(name="Status", value="Undetected ✅", inline=True)
    embed.set_footer(text="Buy Lifetime at xraygamer.sell.app for 24/7 Access")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="links", description="Show official project links")
async def links(interaction: discord.Interaction):
    embed = discord.Embed(title="🔗 XrayGamer Official Links", color=discord.Color.blue())
    embed.add_field(name="🛒 Shop", value="[SellApp Store](https://xraygamer.sell.app/)", inline=False)
    embed.add_field(name="📁 GitHub", value="[Project Hub](https://github.com/XrayGamerOfficial97/XrayGamer-Project-Hub)", inline=False)
    embed.add_field(name="📥 Download", value="[Direct Link](https://drive.google.com/file/d/1b4-7trPriu49TMET8Si-oucpDUUJDXPQ/view?usp=sharing)", inline=False)
    embed.set_footer(text="Precision and Security.")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="admin_add_vip", description="Add a Lifetime VIP Key (Admin Only)")
async def admin_add_vip(interaction: discord.Interaction, key_name: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Access Denied.", ephemeral=True)

    local_keys = load_keys()
    local_keys[key_name] = {
        "user": "VIP_LIFETIME",
        "user_id": None,
        "hwid": None,
        "status": "active",
        "expires_at": "never"
    }
    save_keys(local_keys)
    await interaction.response.send_message(f"✅ VIP Key `{key_name}` added successfully (Lifetime).", ephemeral=True)

@bot.tree.command(name="admin_keys", description="View all keys (Admin Only)")
async def admin_keys(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Access Denied.", ephemeral=True)

    keys = load_keys()
    if not keys:
        return await interaction.response.send_message("📭 Database is empty.", ephemeral=True)

    msg = "### 🔑 LICENSE LIST\n"
    for k, v in keys.items():
        status_icon = "🛑" if v.get("status") == "disabled" else "✅"
        hwid_status = "Bound" if v['hwid'] else "Unused"
        exp = v.get("expires_at", "never")
        msg += f"{status_icon} **{k}** | HWID: `{hwid_status}` | Exp: `{exp}`\n"
        if len(msg) > 1800: break 
    
    await interaction.response.send_message(msg, ephemeral=True)

# --- KOMANDAT E REJA TË SHTUARA (ADMIN ONLY) ---

@bot.tree.command(name="admin_reset_key", description="Reset HWID for a specific key (Admin Only)")
async def admin_reset_key(interaction: discord.Interaction, key_name: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
    
    local_keys = load_keys()
    if key_name in local_keys:
        local_keys[key_name]['hwid'] = None
        save_keys(local_keys)
        await interaction.response.send_message(f"🔄 HWID reset for key `{key_name}`. User can now link a new PC.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Key not found.", ephemeral=True)

@bot.tree.command(name="admin_manage_key", description="Enable or Disable a key (Admin Only)")
@app_commands.choices(action=[
    app_commands.Choice(name="Enable (Open)", value="active"),
    app_commands.Choice(name="Disable (Close)", value="disabled")
])
async def admin_manage_key(interaction: discord.Interaction, key_name: str, action: app_commands.Choice[str]):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
    
    local_keys = load_keys()
    if key_name in local_keys:
        local_keys[key_name]['status'] = action.value
        save_keys(local_keys)
        status_text = "ENABLED" if action.value == "active" else "DISABLED/CLOSED"
        await interaction.response.send_message(f"⚙️ Key `{key_name}` is now **{status_text}**.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Key not found.", ephemeral=True)

# ================= EVENTS =================

@bot.event
async def on_ready():
    print(f'🚀 XrayGamer Bot Online: {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/getkey"))

# NISJA E SERVERIT DHE BOTIT
if __name__ == "__main__":
    # Nis serverin Auth në një thread tjetër
    threading.Thread(target=run_flask, daemon=True).start()
    # Nis botin e Discordit
    bot.run(TOKEN) kete kam ne github 
