import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import uuid
from flask import Flask, request, jsonify
import threading

# Merr Tokenin nga Railway
TOKEN = os.environ.get('DISCORD_TOKEN')

class XrayBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Slash commands synchronized!")

bot = XrayBot()
KEYS_FILE = "keys.json"

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

# ================= SERVERI PER LAUNCHERIN (FLASK) =================
app = Flask('')

@app.route('/check_key', methods=['GET'])
def check_key():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    
    if key in active_keys:
        # Lidhja e HWID per here te pare
        if active_keys[key]['hwid'] is None:
            active_keys[key]['hwid'] = hwid
            save_keys(active_keys)
            return jsonify({"status": "success", "message": "Key linked to your PC!"})
        
        # Verifikimi i HWID
        if active_keys[key]['hwid'] == hwid:
            return jsonify({"status": "success", "message": "Access Granted!"})
        else:
            return jsonify({"status": "error", "message": "Key already used on another PC!"})
            
    return jsonify({"status": "error", "message": "Invalid Key!"})

def run_flask():
    # Railway perdor porten 8080 automatikisht
    app.run(host='0.0.0.0', port=8080)

# ================= KOMANDAT E DISCORD =================

@bot.event
async def on_ready():
    print(f'🚀 XrayGamer Bot is ONLINE as {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="PUBG Utility | /status"
    ))

@bot.tree.command(name="getkey", description="Get your unique installation key")
async def getkey(interaction: discord.Interaction):
    OWNER_ID = 1386797649532948570 
    
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
    
    msg = f"✅ Hello **OWNER**! Your key: `{new_key}`" if interaction.user.id == OWNER_ID else f"✅ Your key: `{new_key}`"
    await interaction.response.send_message(msg, ephemeral=True)

# Nis serverin Flask ne nje "thread" tjeter qe te mos bllokoje botin
threading.Thread(target=run_flask).start()

bot.run(TOKEN)
