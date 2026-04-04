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

# ================= NEW: AUTO SETUP COMMAND (PRO BUILDER) =================

@bot.tree.command(name="setup_pro_server", description="Build the entire professional server structure automatically")
async def setup_pro_server(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Only the Owner can use this!", ephemeral=True)
        return

    await interaction.response.send_message("🛠️ Building Professional Server... Please wait.", ephemeral=True)
    guild = interaction.guild

    # Permissions setups
    view_only = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False, view_channel=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(send_messages=True, view_channel=True)
    }
    chat_allowed = {
        guild.default_role: discord.PermissionOverwrite(send_messages=True, view_channel=True, read_message_history=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(send_messages=True, view_channel=True)
    }

    # Create Categories and Channels
    try:
        # Category 1
        cat_info = await guild.create_category("🛰️ INFORMATION")
        await guild.create_text_channel("┃👋-welcome", category=cat_info, overwrites=view_only)
        await guild.create_text_channel("┃📜-rules", category=cat_info, overwrites=view_only)
        await guild.create_text_channel("┃📢-announcements", category=cat_info, overwrites=view_only)
        await guild.create_text_channel("┃✅-verify-here", category=cat_info, overwrites=view_only)

        # Category 2
        cat_script = await guild.create_category("🚀 XRAY SCRIPT")
        await guild.create_text_channel("┃📂-download", category=cat_script, overwrites=view_only)
        await guild.create_text_channel("┃🔑-get-license", category=cat_script, overwrites=chat_allowed)
        await guild.create_text_channel("┃🆘-technical-support", category=cat_script, overwrites=chat_allowed)

        # Category 3
        cat_comm = await guild.create_category("💬 COMMUNITY")
        await guild.create_text_channel("┃💬-general-chat", category=cat_comm, overwrites=chat_allowed)
        await guild.create_text_channel("┃📸-media-results", category=cat_comm, overwrites=chat_allowed)

        await interaction.followup.send("✅ **SUCCESS:** Your professional server structure is ready!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ **ERROR:** {e}", ephemeral=True)

# ================= EXISTING DISCORD COMMANDS (MOS I PREK) =================

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

@bot.tree.command(name="rules", description="Show the official project rules and access guide")
async def rules(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 XrayGamer Rules & Access Guide",
        description="Follow these mandatory steps to activate your software session:",
        color=discord.Color.gold()
    )
    embed.add_field(name="1️⃣ Subscriber Status", value="Subscribe to [YouTube](https://youtube.com/@xraygamerofficial) to get the role.", inline=False)
    embed.add_field(name="2️⃣ Secure Download", value="Download from [GitHub](https://github.com/XrayGamerOfficial97/XrayGamer-Project-Hub).", inline=False)
    embed.add_field(name="3️⃣ Generate License", value="Use `/getkey` to get your key.", inline=False)
    embed.add_field(name="⚠️ Security Warning", value="Sharing keys results in a **permanent hardware ban**.", inline=False)
    
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    
    embed.set_footer(text="XrayGamer Project Hub | Premium Edition 2026")
    await interaction.response.send_message(embed=embed)

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
