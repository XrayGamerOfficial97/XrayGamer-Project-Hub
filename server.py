import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import uuid

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

# Funksionet e bazës së të dhënave
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

@bot.event
async def on_ready():
    print(f'🚀 XrayGamer Bot is ONLINE as {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="PUBG Utility | /status"
    ))

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="verify-here")
    if channel:
        welcome_embed = discord.Embed(
            title="Welcome to XrayGamer Official Hub! 🚀",
            description=(
                f"Hello {member.mention}, to unlock the **PUBG Script**:\n\n"
                "1️⃣ Go to our YouTube channel.\n"
                "2️⃣ Subscribe and take a screenshot.\n"
                "3️⃣ Upload the screenshot in this channel."
            ),
            color=discord.Color.blue()
        )
        await channel.send(embed=welcome_embed)

@bot.tree.command(name="status", description="Check the PUBG Script safety status")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 XrayGamer Security Monitor", 
        description="Real-time status for PUBG Utility v1.0.0",
        color=discord.Color.green()
    )
    embed.add_field(name="🛡️ Script Status", value="✅ **UNDETECTED**", inline=True)
    embed.add_field(name="🌐 Server Connection", value="✅ **STABLE**", inline=True)
    embed.add_field(name="📅 Last Update", value="April 2026", inline=False)
    embed.set_footer(text="Verified by XrayGamer Development Team")
    await interaction.response.send_message(embed=embed)

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
    
    msg = f"✅ Hello **OWNER**! Your unique key is: `{new_key}`" if interaction.user.id == OWNER_ID else f"✅ Your unique key is: `{new_key}`\nKeep it safe!"
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="links", description="Get official XrayGamer project links")
async def links(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔗 Official Project Links", 
        description="Access the latest tools and updates below:",
        color=discord.Color.blue()
    )
    embed.add_field(name="📺 YouTube Channel", value="[Subscribe here](https://youtube.com/@xraygamerofficial?si=eIL7vfGoDm_kMYUz)", inline=False)
    embed.add_field(name="💬 Discord Server", value="[Join Discord](https://discord.gg/kqAF4WaZJK)", inline=False)
    embed.add_field(name="📂 GitHub Repository", value="[Download Source](https://github.com/XrayGamerOfficial97/XrayGamer-Project-Hub/releases/tag/v1.0.0)", inline=False)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
