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

# --- KEY PERSISTENCE (MOS E PREK) ---
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

# ================= FLASK AUTH SERVER (PER LAUNCHER - MOS E PREK) =================
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
        if active_keys[key]['hwid'] is None:
            active_keys[key]['hwid'] = hwid
            save_keys(active_keys)
            return jsonify({"status": "success", "message": "Key bound to your hardware!"})
        
        if active_keys[key]['hwid'] == hwid:
            return jsonify({"status": "success", "message": "Access Granted!"})
        else:
            return jsonify({"status": "error", "message": "Key bound to another PC!"})
            
    return jsonify({"status": "error", "message": "Invalid License Key!"})

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= NEW: ADMIN MONITORING COMMAND =================

@bot.tree.command(name="admin_keys", description="Shiko të gjithë çelësat e gjeneruar (Vetëm Owner)")
async def admin_keys(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Nuk ke leje për këtë komandë!", ephemeral=True)
        return

    # Rifreskojmë listën nga skedari për siguri
    current_keys = load_keys()
    
    if not current_keys:
        await interaction.response.send_message("📭 Nuk ka asnjë çelës të gjeneruar në databazë.", ephemeral=True)
        return

    mesazhi = "### 🔑 LISTA E LICENCAVE AKTIVE\n"
    mesazhi += "--------------------------------------\n"
    
    for key, data in current_keys.items():
        user = data.get("user", "Unknown")
        hwid = data.get("hwid")
        status = f"✅ **Bound:** `{hwid[:10]}...`" if hwid else "⏳ **Unused**"
        mesazhi += f"**Key:** `{key}`\n👤 **User:** {user}\n🛡️ **Status:** {status}\n\n"

    # E dërgojmë "ephemeral" që ta shohësh vetëm TI
    await interaction.response.send_message(mesazhi, ephemeral=True)

# ================= SERVER SETUP COMMAND =================

@bot.tree.command(name="setup_pro_server", description="Build the entire professional server structure automatically")
async def setup_pro_server(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Only the Owner can use this!", ephemeral=True)
        return

    await interaction.response.send_message("🛠️ Building Professional Server... Please wait.", ephemeral=True)
    guild = interaction.guild

    view_only = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False, view_channel=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(send_messages=True, view_channel=True)
    }
    chat_allowed = {
        guild.default_role: discord.PermissionOverwrite(send_messages=True, view_channel=True, read_message_history=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(send_messages=True, view_channel=True)
    }

    try:
        cat_info = await guild.create_category("🛰️ INFORMATION")
        await guild.create_text_channel("┃👋-welcome", category=cat_info, overwrites=view_only)
        await guild.create_text_channel("┃📜-rules", category=cat_info, overwrites=view_only)
        await guild.create_text_channel("┃📢-announcements", category=cat_info, overwrites=view_only)
        await guild.create_text_channel("┃✅-verify-here", category=cat_info, overwrites=view_only)

        cat_script = await guild.create_category("🚀 XRAY SCRIPT")
        await guild.create_text_channel("┃📂-download", category=cat_script, overwrites=view_only)
        await guild.create_text_channel("┃🔑-get-license", category=cat_script, overwrites=chat_allowed)
        await guild.create_text_channel("┃🆘-technical-support", category=cat_script, overwrites=chat_allowed)

        cat_comm = await guild.create_category("💬 COMMUNITY")
        await guild.create_text_channel("┃💬-general-chat", category=cat_comm, overwrites=chat_allowed)
        await guild.create_text_channel("┃📸-media-results", category=cat_comm, overwrites=chat_allowed)

        await interaction.followup.send("✅ **SUCCESS:** Server structure ready!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ **ERROR:** {e}", ephemeral=True)

# ================= EXISTING COMMANDS =================

@bot.event
async def on_ready():
    print(f'🚀 XrayGamer Bot is ONLINE as {bot.user}')
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="GitHub | /rules"
    ))

@bot.tree.command(name="getkey", description="Generate your unique installation key")
async def getkey(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        role = discord.utils.get(interaction.guild.roles, name="Subscriber")
        if role not in interaction.user.roles:
            await interaction.response.send_message("❌ **Error:** You must be a **Subscriber** to get a key!", ephemeral=True)
            return

    # Rifreskojmë listën lokale para kontrollit
    local_keys = load_keys()
    for k, v in local_keys.items():
        if v.get("user_id") == interaction.user.id:
            await interaction.response.send_message(f"⚠️ You already have a key: `{k}`", ephemeral=True)
            return

    new_key = f"XRAY-{str(uuid.uuid4())[:8].upper()}"
    local_keys[new_key] = {
        "user": str(interaction.user),
        "user_id": interaction.user.id,
        "hwid": None,
        "status": "active"
    }
    save_keys(local_keys)
    active_keys.update(local_keys) # Update global memory
    
    msg = f"✅ **OWNER:** Your key: `{new_key}`" if interaction.user.id == OWNER_ID else f"✅ Your unique key: `{new_key}`"
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="rules", description="Show official project rules")
async def rules(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 XrayGamer Protocol", color=discord.Color.gold())
    embed.add_field(name="Steps", value="Subscribe -> Verify -> Download -> Key.", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="links", description="Official project links")
async def links(interaction: discord.Interaction):
    embed = discord.Embed(title="🚀 Official Resources", color=discord.Color.blue())
    embed.add_field(name="GitHub", value="[Repository](https://github.com/XrayGamerOfficial97/XrayGamer-Project-Hub)", inline=False)
    await interaction.response.send_message(embed=embed)

# Run Flask in background
threading.Thread(target=run_flask, daemon=True).start()

bot.run(TOKEN)
