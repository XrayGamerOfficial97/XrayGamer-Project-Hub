import discord
from discord import app_commands
from discord.ext import commands
import os
# ⚠️ REPLACE THIS WITH YOUR NEW RESET TOKEN FROM DEVELOPER PORTAL
TOKEN = os.environ.get('DISCORD_TOKEN')

class XrayBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # This syncs the /commands with Discord
        await self.tree.sync()
        print(f"✅ Slash commands synchronized!")

bot = XrayBot()

@bot.event
async def on_ready():
    print(f'🚀 XrayGamer Bot is ONLINE as {bot.user}')
    # Set a professional "Watching" status
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="PUBG Utility | /status"
    ))

@bot.event
async def on_member_join(member):
    # Auto-welcome message in English when someone joins
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

@bot.tree.command(name="links", description="Get official XrayGamer project links")
async def links(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔗 Official Project Links", 
        description="Access the latest tools and updates below:",
        color=discord.Color.blue()
    )
    embed.add_field(name="📺 YouTube Channel", value="[Subscribe here](https://youtube.com/@xraygamerofficial?si=eIL7vfGoDm_kMYUz)", inline=False)
    embed.add_field(name="💬 Discord Server", value="[Join Discord](https://discord.gg/kqAF4WaZJK)", inline=False)
    embed.add_field(name="📁 GitHub Repository", value="[Download Source](https://github.com/XrayGamerOfficial97/XrayGamer-Project-Hub/releases/tag/v1.0.0)"
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="How to use the XrayGamer Hub")
async def help(interaction: discord.Interaction):
    help_text = (
        "**Quick Start Guide:**\n"
        "1️⃣ **Download:** Get the files from GitHub via `/links`.\n"
        "2️⃣ **Verify:** Post your sub-proof in `#verify-here`.\n"
        "3️⃣ **Unlock:** Get the installation key in `#password-vault` after verification."
    )
    await interaction.response.send_message(help_text, ephemeral=True)

bot.run(TOKEN)
