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
        await self.tree.sync()
        print(f"✅ Slash commands synchronized globally!")

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

# ================= FLASK AUTH SERVER (FOR LAUNCHER) =================
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
    
    if key in active_keys:
        # Hardware Lock on first use
        if active_keys[key]['hwid'] is None:
            active_keys[key]['hwid'] = hwid
            save_keys(active_keys)
            return jsonify({"status": "success", "message": "Key bound to your hardware!"})
        
        # HWID Verification
        if active_keys[key]['hwid'] == hwid:
            return jsonify({"status": "success", "message": "Access Granted!"})
        else:
            return jsonify({"status": "error", "message": "Key bound to another PC!"})
            
    return jsonify({"status": "error", "message": "Invalid License Key!"})

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= DISCORD COMMANDS =================

@bot.event
async def on_ready():
    print(f'🚀 XrayGamer Bot is ONLINE as {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="GitHub | /links"
    ))

@bot.tree.command(name="getkey", description="Generate your unique installation key")
async def getkey(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        role = discord.utils.get(interaction.guild.roles, name="Subscriber")
        if role not in interaction.user.roles:
            await interaction.response.send_message("❌ **Error:** You must be a **Subscriber** to get a key!", ephemeral=True)
            return

    for k, v in active_keys.items():
        if v.get("user_id") == interaction.user.id:
            await interaction.response.send_message(f"⚠️ You already have a key: `{k}`", ephemeral=True)
            return

    new_key = f"XRAY-{str(uuid.uuid4())[:8].upper()}"
    active_keys[new_key] = {
        "user": str(interaction.user),
        "user_id": interaction.user.id,
        "hwid": None,
        "status": "active"
    }
    save_keys(active_keys)
    
    msg = f"✅ **OWNER:** Your key: `{new_key}`" if interaction.user.id == OWNER_ID else f"✅ Your unique key: `{new_key}`"
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="links", description="Official project links and download guide")
async def links(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🚀 XrayGamer Project Hub - Official Resources",
        description="Visit the repository for the latest AI models and download links.",
        color=discord.Color.blue()
    )
    embed.add_field(name="📺 YouTube", value="[Subscribe](https://youtube.com/@xraygamerofficial)", inline=True)
    embed.add_field(name="💬 Discord", value="[Join Server](https://discord.gg/ZTzRKywZJd)", inline=True)
    embed.add_field(name="📁 GitHub Repository", value="[Download & README](https://github.com/XrayGamerOfficial97/XrayGamer-Project-Hub)", inline=False)
    
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    
    embed.set_footer(text="XrayGamer Official | © 2026")
    await interaction.response.send_message(embed=embed)

# Run Flask in background
threading.Thread(target=run_flask, daemon=True).start()

bot.run(TOKEN)
