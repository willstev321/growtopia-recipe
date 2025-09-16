import discord
from discord.ext import commands, tasks
import os
import threading
import subprocess
import time
from dotenv import load_dotenv
from database import init_db, get_recipe, get_all_items, get_item_details, search_items, get_item_image_url
from items_parser import fetch_and_parse_items, load_all_items

# Load environment variables dari file .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

intents = discord.Intents.default()
intents.message_content = True

# Nonaktifkan help command bawaan agar bisa menggunakan custom help
bot = commands.Bot(
    command_prefix="*", 
    intents=intents,
    help_command=None
)

# Daftar channel yang diizinkan (whitelist)
ALLOWED_CHANNELS = [
    1417382043527942204,
]

# URL channel khusus
SPECIAL_CHANNEL_URL = "https://discord.com/channels/1414500944200204379/1417382043527942204"

def get_channel_mention(channel_id):
    return f"<#{channel_id}>"

def format_recipe_with_images(recipe_text):
    """Format recipe text dengan menambahkan gambar untuk setiap komponen"""
    if not recipe_text:
        return "Tidak ada recipe"
    
    components = recipe_text.split(' + ')
    formatted_components = []
    
    for component in components:
        component = component.strip()
        image_url = get_item_image_url(component)
        
        if image_url:
            formatted_components.append(f"[{component}]({image_url})")
        else:
            formatted_components.append(component)
    
    return " + ".join(formatted_components)

def run_item_parser_periodically():
    while True:
        try:
            print("🔄 Menjalankan item_parser.py...")
            result = subprocess.run(["python", "item_parser.py"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ item_parser.py berhasil dijalankan")
            else:
                print(f"❌ Error menjalankan item_parser.py: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Exception dalam run_item_parser_periodically: {e}")
        
        time.sleep(86400)

def initialize_database():
    try:
        print("🔄 Menginisialisasi database...")
        init_db()
        
        if len(get_all_items()) == 0:
            print("🔄 Loading items to database...")
            load_all_items()
            
        print("✅ Database berhasil diinisialisasi")
    except Exception as e:
        print(f"❌ Error dalam initialize_database: {e}")

def is_channel_allowed(channel_id):
    return channel_id in ALLOWED_CHANNELS

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"👥 Connected to {len(bot.guilds)} guild(s)")
    print(f"📋 Channel yang diizinkan: {ALLOWED_CHANNELS}")
    check_items_update.start()

@bot.check
async def channel_check(ctx):
    if not is_channel_allowed(ctx.channel.id):
        embed = discord.Embed(
            title="🚫 Channel Tidak Diizinkan",
            description="Bot ini hanya dapat digunakan di channel khusus untuk menjaga kerapian server.",
            color=discord.Color.red()
        )
        
        target_channel = get_channel_mention(ALLOWED_CHANNELS[0])
        
        embed.add_field(
            name="📍 Channel yang Diizinkan",
            value=f"Silakan kunjungi {target_channel} untuk menggunakan bot ini\nAtau klik link langsung: {SPECIAL_CHANNEL_URL}",
            inline=False
        )
        
        embed.set_footer(text="Growtopia Recipe Bot • Terima kasih atas pengertiannya!")
        embed.set_thumbnail(url="https://i.imgur.com/7Q7Qe0M.png")
        
        await ctx.send(embed=embed)
        return False
    return True

@tasks.loop(hours=24)
async def check_items_update():
    try:
        new_items = fetch_and_parse_items()
        if new_items:
            print(f"🆕 {len(new_items)} item baru ditemukan!")
            for guild in bot.guilds:
                for allowed_channel_id in ALLOWED_CHANNELS:
                    channel = bot.get_channel(allowed_channel_id)
                    if channel:
                        for item in new_items:
                            embed = discord.Embed(
                                title="🆕 ITEM BARU DITEMUKAN!",
                                description=f"**{item['name']}** telah ditambahkan ke database",
                                color=discord.Color.gold()
                            )
                            
                            embed.add_field(
                                name="📊 Detail Item",
                                value=f"**Tier:** {item.get('tier', 'N/A')}\n**Recipe:** {item.get('recipe','Tidak ada recipe')}",
                                inline=False
                            )
                            
                            embed.set_footer(text="Growtopia Recipe Bot • Update Otomatis")
                            await channel.send(embed=embed)
    except Exception as e:
        print(f"❌ Error in check_items_update: {e}")

@bot.command(name="recipe")
async def recipe(ctx, *, item_name: str):
    try:
        recipe_text = get_recipe(item_name)
        
        if recipe_text:
            item_details = get_item_details(item_name)
            if item_details:
                formatted_recipe = format_recipe_with_images(recipe_text)
                
                embed = discord.Embed(
                    title=f"📦 RECIPE: {item_details['name'].upper()}",
                    description=f"**Tier:** {item_details.get('tier', 'N/A')} | **ID:** {item_details['id']}",
                    color=discord.Color.green()
                )
                
                if item_details.get('image_url'):
                    embed.set_thumbnail(url=item_details['image_url'])
                
                embed.add_field(
                    name="📋 **Recipe**",
                    value=formatted_recipe,
                    inline=False
                )
                
                embed.set_footer(text="Growtopia Recipe Bot • Info terkini")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"📦 Recipe untuk **{item_name}**:\n```{recipe_text}```")
        else:
            suggestions = search_items(item_name)
            if suggestions:
                embed = discord.Embed(
                    title="❌ Item Tidak Ditemukan",
                    description=f"Tidak ditemukan recipe untuk **{item_name}**",
                    color=discord.Color.orange()
                )
                
                suggestion_list = "\n".join([f"• {name}" for _, name in suggestions[:5]])
                embed.add_field(
                    name="💡 **Mungkin maksud Anda:**",
                    value=suggestion_list,
                    inline=False
                )
                
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Item Tidak Ditemukan",
                    description=f"Tidak ditemukan recipe untuk **{item_name}**",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="⚠️ Error",
            description=f"Terjadi kesalahan saat memproses permintaan: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Command lainnya tetap sama seperti yang Anda berikan...
# (search, iteminfo, help, on_command_error tetap tidak berubah)

if __name__ == "__main__":
    initialize_database()
    
    parser_thread = threading.Thread(target=run_item_parser_periodically, daemon=True)
    parser_thread.start()
    print("✅ Item parser thread started")
    
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        print("❌ ERROR: DISCORD_BOT_TOKEN tidak ditemukan di environment variables!")
        print("💡 Pastikan file .env ada dan berisi: DISCORD_BOT_TOKEN=your_token_here")
        exit(1)

    print("🚀 Starting bot...")
    bot.run(token)
