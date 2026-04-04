import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import uuid
from flask import Flask, request, jsonify
import threading

# --- CONFIGURATION ---
# Railway will automatically provide the DISCORD_TOKEN from Variables
TOKEN = os.environ.get('DISCORD_TOKEN')
OWNER_ID = 1386797649532948570 
KEYS_FILE = "keys.json"

# --- BOT INITIALIZATION ---
class XrayBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Synchronizes slash commands with Discord
        await self.tree.sync()
        print(f"✅ Slash commands synchronized globally!")

bot = XrayBot()

# --- KEY MANAGEMENT SYSTEM ---
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

# Load existing keys into memory
active_keys = load_keys()

# --- FLASK AUTH SERVER (FOR LAUNCHER) ---
app = Flask('')

@app.route('/')
def home():
    return "XrayGamer Authentication Server is Online."

@app.route('/check_key', methods=['GET'])
def check_key():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    
    if not key or not hwid:
        return jsonify({"status": "error", "message": "Missing key or HWID parameters!"}), 400
    
    if key in active_keys:
        # Hardware Lock (Binding) on first-time use
        if active_keys[key]['hwid'] is None:
            active_keys[key]['hwid'] = hwid
            save_keys(active_keys)
            return jsonify({"status": "success", "message": "License successfully bound to your Hardware ID!"})
        
        # HWID Verification for subsequent uses
        if active_keys[key]['hwid'] == hwid:
            return jsonify({"status": "success", "message": "Access Granted! System Initializing..."})
        else:
            return jsonify({"status": "error", "message": "Security Alert: This key is bound to a different PC!"})
            
    return jsonify({"status": "error", "message": "Invalid or Expired License Key!"})

def run_flask():
    # Railway assigns a dynamic port via the PORT variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- DISCORD COMMANDS ---
@bot.event
async def on_ready():
    print(f'🚀 XrayGamer Bot is ACTIVE as {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="GitHub | /links"
    ))

@bot.tree.command(name="getkey", description="Generate your unique AI Hub license key")
async def getkey(interaction: discord.Interaction):
    # Permission Check (Owner or Subscriber Role)
    if interaction.user.id != OWNER_ID:
        role = discord.utils.get(interaction.guild.roles, name="Subscriber")
        if role not in interaction.user.roles:
            await interaction.response.send_message("❌ **Access Denied:** You need the **Subscriber** role to get a key!", ephemeral=True)
            return

    # Check if user already has a key assigned
    for k, v in active_keys.items():
        if v.get("user_id") == interaction.user.id:
            await interaction.response.send_message(f"⚠️ **Notice:** You already have an active key: `{k}`", ephemeral=True)
            return

    # Generate Secure Unique Key (Format: XRAY-XXXXXXX)
    new_key = f"XRAY-{str(uuid.uuid4())[:8].upper()}"
    active_keys[new_key] = {
        "user": str(interaction.user),
        "user_id": interaction.user.id,
        "hwid": None,
        "status": "active"
    }
    save_keys(active_keys)
    
    msg = f"✅ **OWNER AUTH:** Your Master Key: `{new_key}`" if interaction.user.id == OWNER_ID else f"✅ **Success!** Your license key: `{new_key}`"
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="links", description="Official download links and project documentation")
async def links(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🚀 XrayGamer Project Hub - Official Resources",
        description="Please visit the GitHub repository for the full download and setup instructions.",
        color=discord.Color.blue()
    )
    embed.add_field(name="📺 YouTube Channel", value="[Official Updates](https://youtube.com/@xraygamerofficial)", inline=True)
    embed.add_field(name="💬 Discord Community", value="[Join Server](https://discord.gg/ZTzRKywZJd)", inline=True)
    embed.add_field(name="📁 GitHub Repository", value="[Download & README Guide](https://github.com/XrayGamerOfficial97/XrayGamer-Project-Hub)", inline=False)
    
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    
    embed.set_footer(text="Developed by XrayGamer Official | © 2026")
    
    await interaction.response.send_message(embed=embed)

# Start Flask in a background thread
threading.Thread(target=run_flask, daemon=True).start()

# Launch Bot
bot.run(TOKEN)
