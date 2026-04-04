import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import uuid
from flask import Flask, request, jsonify
import threading

# --- CONFIGURATION ---
TOKEN = os.environ.get('DISCORD_TOKEN')
OWNER_ID = 1386797649532948570 
KEYS_FILE = "keys.json"

class XrayBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"✅ Slash commands synchronized: {len(synced)} commands found.")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

bot = XrayBot()

# --- KEY PERSISTENCE ---
def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

active_keys = load_keys()

# ================= FLASK AUTH SERVER =================
app = Flask('')

@app.route('/')
def home():
    return "XrayGamer Auth Server is Online."

@app.route('/check_key', methods=['GET'])
def check_key():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    
    if not key or not hwid:
        return jsonify({"status": "error", "message": "Missing parameters!"}), 400
    
    keys = load_keys()
    
    if key in keys:
        if keys[key]['hwid'] is None:
            keys[key]['hwid'] = hwid
            save_keys(keys)
            return jsonify({"status": "success", "message": "Key bound to your hardware!"})
        
        if keys[key]['hwid'] == hwid:
            return jsonify({"status": "success", "message": "Access Granted!"})
        else:
            return jsonify({"status": "error", "message": "Key bound to another PC!"})
            
    return jsonify({"status": "error", "message": "Invalid License Key!"})

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= RESET COMMANDS (ENGLISH) =================

@bot.tree.command(name="reset_my_key", description="Reset the HWID for your own key")
async def reset_my_key(interaction: discord.Interaction):
    keys = load_keys()
    found = False
    for key in keys:
        if keys[key]['user_id'] == interaction.user.id:
            keys[key]['hwid'] = None
            found = True
            break
    
    if found:
        save_keys(keys)
        await interaction.response.send_message("✅ **Success:** Your HWID has been reset. You can now login from a new device.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ **Error:** No active key found linked to your account.", ephemeral=True)

@bot.tree.command(name="reset_user_key", description="Reset HWID for a specific key (Admin Only)")
async def reset_user_key(interaction: discord.Interaction, key_to_reset: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ **Error:** Access denied.", ephemeral=True)
        return

    keys = load_keys()
    if key_to_reset in keys:
        keys[key_to_reset]['hwid'] = None
        save_keys(keys)
        await interaction.response.send_message(f"✅ **Admin:** HWID for key `{key_to_reset}` has been reset successfully.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ **Error:** This key does not exist in the database.", ephemeral=True)

# ================= ADMIN MONITORING =================

@bot.tree.command(name="admin_keys", description="View all generated keys (Owner Only)")
async def admin_keys(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Access denied.", ephemeral=True)
        return

    current_keys = load_keys()
    if not current_keys:
        await interaction.response.send_message("📭 Database is empty.", ephemeral=True)
        return

    mesazhi = "### 🔑 ACTIVE LICENSES LIST\n"
    for key, data in current_keys.items():
        user = data.get("user", "Unknown")
        hwid = data.get("hwid")
        status = "✅ `Bound`" if hwid else "⏳ `Unused`"
        mesazhi += f"**Key:** `{key}` | **User:** {user} | **Status:** {status}\n"

    await interaction.response.send_message(mesazhi, ephemeral=True)

# ================= GET KEY COMMAND (ENGLISH) =================

@bot.tree.command(name="getkey", description="Generate your unique installation key")
async def getkey(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        role = discord.utils.get(interaction.guild.roles, name="Subscriber")
        if role not in interaction.user.roles:
            await interaction.response.send_message("❌ **Error:** You must have the **Subscriber** role to generate a key!", ephemeral=True)
            return

    local_keys = load_keys()
    for k, v in local_keys.items():
        if v.get("user_id") == interaction.user.id:
            await interaction.response.send_message(f"⚠️ **Notice:** You already have an active key: `{k}`", ephemeral=True)
            return

    new_key = f"XRAY-{str(uuid.uuid4())[:8].upper()}"
    local_keys[new_key] = {
        "user": str(interaction.user),
        "user_id": interaction.user.id,
        "hwid": None,
        "status": "active"
    }
    save_keys(local_keys)
    
    await interaction.response.send_message(f"✅ **Success:** Your unique key is: `{new_key}`\n\n*Note: This key will bind to the first PC that uses it.*", ephemeral=True)

# ================= SETUP & EVENTS =================

@bot.event
async def on_ready():
    print(f'🚀 Bot Online: {bot.user}')
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="GitHub | /links"))

@bot.tree.command(name="links", description="Show official project links")
async def links(interaction: discord.Interaction):
    embed = discord.Embed(title="🚀 XrayGamer Official Resources", color=discord.Color.blue())
    
    # Linku i GitHub
    embed.add_field(name="📁 GitHub", value="[Repository](https://github.com/XrayGamerOfficial97/XrayGamer-Project-Hub)", inline=False)
    
    # Linku i YouTube (I RI)
    embed.add_field(name="🎥 YouTube", value="[Official Channel](https://youtube.com/@xraygamerofficial?si=O-gcrKKFQ2WlXypR)", inline=False)
    
    # Linku i Download (I RI)
    embed.add_field(name="📥 Download", value="[Google Drive Link](https://drive.google.com/file/d/1b4-7trPriu49TMET8Si-oucpDUUJDXPQ/view?usp=sharing)", inline=False)
    
    embed.set_footer(text="Precision in every line of code.")
    await interaction.response.send_message(embed=embed)

# Run Flask & Bot
threading.Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
