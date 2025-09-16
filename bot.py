import discord
from discord.ext import commands, tasks
import os
import threading
import subprocess
import time
from dotenv import load_dotenv
from database import init_db, get_recipe, get_all_items, get_item_details, search_items
from items_parser import fetch_and_parse_items, load_all_items

# Load environment variables dari file .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

intents = discord.Intents.default()
intents.message_content = True

# Nonaktifkan help command bawaan agar bisa menggunakan custom help
bot = commands.Bot(
    command_prefix="*",  # DIUBAH: gunakan * sebagai prefix
    intents=intents,
    help_command=None
)

def run_item_parser_periodically():
    """Jalankan item_parser.py secara periodic setiap 24 jam"""
    while True:
        try:
            print("🔄 Menjalankan item_parser.py...")
            # Gunakan subprocess untuk menjalankan script terpisah
            result = subprocess.run(["python", "item_parser.py"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ item_parser.py berhasil dijalankan")
                if result.stdout:
                    print(f"Output: {result.stdout}")
            else:
                print(f"❌ Error menjalankan item_parser.py: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Exception dalam run_item_parser_periodically: {e}")
        
        # Tunggu 24 jam sebelum menjalankan lagi
        time.sleep(86400)

def initialize_database():
    """Jalankan inisialisasi database"""
    try:
        print("🔄 Menginisialisasi database...")
        # Inisialisasi DB
        init_db()
        
        # Load items ke database jika belum ada
        if len(get_all_items()) == 0:
            print("🔄 Loading items to database...")
            load_all_items()
            
        print("✅ Database berhasil diinisialisasi")
    except Exception as e:
        print(f"❌ Error dalam initialize_database: {e}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"👥 Connected to {len(bot.guilds)} guild(s)")
    
    check_items_update.start()

# Background task untuk cek item baru
@tasks.loop(hours=24)
async def check_items_update():
    try:
        new_items = fetch_and_parse_items()
        if new_items:
            print(f"🆕 {len(new_items)} item baru ditemukan!")
            for guild in bot.guilds:
                channel = discord.utils.get(
                    guild.text_channels, name="growtopia-news"
                )
                if channel:
                    for item in new_items:
                        await channel.send(
                            f"🆕 **Item Baru!**\n"
                            f"**{item['name']}** (Tier {item.get('tier', 'N/A')})\n"
                            f"📋 Recipe: {item.get('recipe','Tidak ada recipe')}"
                        )
                    break
    except Exception as e:
        print(f"❌ Error in check_items_update: {e}")

# Command lihat recipe
@bot.command(name="recipe")
async def recipe(ctx, *, item_name: str):
    try:
        # Cari item dengan pencarian case-insensitive
        recipe_text = get_recipe(item_name)
        
        if recipe_text:
            # Dapatkan detail lengkap item
            item_details = get_item_details(item_name)
            if item_details:
                tier_info = f" (Tier {item_details['tier']})" if item_details.get('tier') else ""
                await ctx.send(
                    f"📦 **Recipe untuk {item_details['name']}{tier_info}:**\n"
                    f"```{recipe_text}```\n"
                    f"🆔 ID: {item_details['id']}"
                )
            else:
                await ctx.send(f"📦 Recipe untuk **{item_name}**:\n```{recipe_text}```")
        else:
            # Berikan saran jika item tidak ditemukan
            suggestions = search_items(item_name)
            if suggestions:
                suggestion_list = "\n".join([f"• {name}" for _, name in suggestions[:5]])
                await ctx.send(
                    f"❌ Tidak ditemukan recipe untuk **{item_name}**\n"
                    f"💡 Mungkin maksud Anda:\n{suggestion_list}"
                )
            else:
                await ctx.send(f"❌ Tidak ditemukan recipe untuk **{item_name}**")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# Command cari item
@bot.command(name="search")
async def search(ctx, *, keyword: str):
    try:
        items = search_items(keyword)
        if items:
            limited_results = items[:8]  # Batasi hasil menjadi 8 item
            result_text = "\n".join([f"• {name}" for _, name in limited_results])
            
            more_text = ""
            if len(items) > 8:
                more_text = f"\n... dan {len(items) - 8} item lainnya"
                
            await ctx.send(
                f"🔍 Ditemukan **{len(items)}** item untuk '{keyword}':\n"
                f"{result_text}{more_text}"
            )
        else:
            await ctx.send(f"❌ Tidak ada item yang cocok dengan '{keyword}'")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# Command info item lengkap
@bot.command(name="iteminfo")
async def iteminfo(ctx, *, item_name: str):
    try:
        item_details = get_item_details(item_name)
        if item_details:
            tier_info = f"Tier {item_details['tier']}" if item_details.get('tier') else "Tier tidak diketahui"
            
            embed = discord.Embed(
                title=f"🔍 {item_details['name']}",
                description=f"**{tier_info}**\n🆔 ID: {item_details['id']}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📋 Recipe",
                value=item_details['recipe'] if item_details['recipe'] else "Tidak ada recipe",
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Tidak ditemukan informasi untuk **{item_name}**")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# Command help
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 Growtopia Recipe Bot Help",
        description="Berikut adalah daftar command yang tersedia:",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="🔍 Pencarian Item",
        value="• `*recipe [nama_item]` - Cari recipe item\n• `*search [keyword]` - Cari item berdasarkan keyword\n• `*iteminfo [nama_item]` - Info lengkap tentang item",  # DIUBAH: * sebagai prefix
        inline=False
    )
    
    embed.add_field(
        name="💡 Tips",
        value="• Gunakan huruf besar/kecil bebas, bot akan tetap memahami\n• Bot mendukung pencarian partial (sebagian nama item)",
        inline=False
    )
    
    embed.set_footer(text="Bot Growtopia Recipe")
    
    await ctx.send(embed=embed)

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            "❌ Command tidak ditemukan. Gunakan `*help` untuk melihat daftar command yang tersedia."  # DIUBAH: * sebagai prefix
        )
    else:
        await ctx.send(f"❌ Terjadi error: {error}")

# Jalankan bot
if __name__ == "__main__":
    # Inisialisasi database pertama
    initialize_database()
    
    # Jalankan item_parser di thread terpisah (akan berjalan setiap 24 jam)
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
