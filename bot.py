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
    command_prefix="*", 
    intents=intents,
    help_command=None
)

# Daftar channel yang diizinkan (whitelist)
ALLOWED_CHANNELS = [
    1417382043527942204,  # Channel ID dari link Discord Anda
    # Tambahkan channel ID lain jika diperlukan
]

# URL channel khusus
SPECIAL_CHANNEL_URL = "https://discord.com/channels/1414500944200204379/1417382043527942204"

def get_channel_mention(channel_id):
    """Membuat mention/link untuk channel yang bisa diklik"""
    return f"<#{channel_id}>"

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

def is_channel_allowed(channel_id):
    """Cek apakah channel diizinkan untuk menggunakan bot"""
    return channel_id in ALLOWED_CHANNELS

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"👥 Connected to {len(bot.guilds)} guild(s)")
    
    # Tampilkan channel yang diizinkan
    print(f"📋 Channel yang diizinkan: {ALLOWED_CHANNELS}")
    
    check_items_update.start()

@bot.check
async def channel_check(ctx):
    """Global check untuk memverifikasi bahwa command dieksekusi di channel yang diizinkan"""
    if not is_channel_allowed(ctx.channel.id):
        # Buat embed redirect yang menarik
        embed = discord.Embed(
            title="🚫 Channel Tidak Diizinkan",
            description="Bot ini hanya dapat digunakan di channel khusus untuk menjaga kerapian server.",
            color=discord.Color.red()
        )
        
        # Dapatkan channel tujuan yang bisa diklik
        target_channel = get_channel_mention(ALLOWED_CHANNELS[0])
        
        embed.add_field(
            name="📍 Channel yang Diizinkan",
            value=f"Silakan kunjungi {target_channel} untuk menggunakan bot ini\n"
                  f"Atau klik link langsung: {SPECIAL_CHANNEL_URL}",
            inline=False
        )
        
        embed.set_footer(text="Growtopia Recipe Bot • Terima kasih atas pengertiannya!")
        embed.set_thumbnail(url="https://i.imgur.com/7Q7Qe0M.png")  # Ganti dengan URL gambar sesuai tema
        
        await ctx.send(embed=embed)
        return False
    return True

# Background task untuk cek item baru
@tasks.loop(hours=24)
async def check_items_update():
    try:
        new_items = fetch_and_parse_items()
        if new_items:
            print(f"🆕 {len(new_items)} item baru ditemukan!")
            for guild in bot.guilds:
                # Cari channel yang diizinkan
                for allowed_channel_id in ALLOWED_CHANNELS:
                    channel = bot.get_channel(allowed_channel_id)
                    if channel:
                        for item in new_items:
                            # Buat embed untuk item baru
                            embed = discord.Embed(
                                title="🆕 ITEM BARU DITEMUKAN!",
                                description=f"**{item['name']}** telah ditambahkan ke database",
                                color=discord.Color.gold()
                            )
                            
                            embed.add_field(
                                name="📊 Detail Item",
                                value=f"**Tier:** {item.get('tier', 'N/A')}\n"
                                      f"**Recipe:** {item.get('recipe','Tidak ada recipe')}",
                                inline=False
                            )
                            
                            embed.set_footer(text="Growtopia Recipe Bot • Update Otomatis")
                            
                            await channel.send(embed=embed)
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
                # Buat embed dengan desain premium
                embed = discord.Embed(
                    title=f"📦 RECIPE: {item_details['name'].upper()}",
                    description=f"**Tier:** {item_details.get('tier', 'N/A')} | **ID:** {item_details['id']}",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📋 **seeds recipe**",
                    value=f"```yaml\n{recipe_text}```",
                    inline=False
                )
                
                embed.set_footer(text="Growtopia Recipe Bot • Info terkini")
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"📦 Recipe untuk **{item_name}**:\n```{recipe_text}```")
        else:
            # Berikan saran jika item tidak ditemukan
            suggestions = search_items(item_name)
            if suggestions:
                # Buat embed untuk suggestions
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
        # Embed untuk error
        embed = discord.Embed(
            title="⚠️ Error",
            description=f"Terjadi kesalahan saat memproses permintaan: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Command cari item
@bot.command(name="search")
async def search(ctx, *, keyword: str):
    try:
        items = search_items(keyword)
        if items:
            limited_results = items[:8]  # Batasi hasil menjadi 8 item
            
            # Buat embed untuk hasil pencarian
            embed = discord.Embed(
                title=f"🔍 HASIL PENCARIAN: '{keyword.upper()}'",
                description=f"Ditemukan **{len(items)}** item yang cocok",
                color=discord.Color.blue()
            )
            
            result_text = "\n".join([f"• {name}" for _, name in limited_results])
            embed.add_field(
                name="📋 Item yang Ditemukan",
                value=result_text,
                inline=False
            )
            
            if len(items) > 8:
                embed.add_field(
                    name="ℹ️ Info",
                    value=f"Menampilkan 8 dari {len(items)} item. Gunakan pencarian lebih spesifik untuk hasil yang lebih tepat.",
                    inline=False
                )
                
            embed.set_footer(text="Growtopia Recipe Bot • Pencarian")
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="🔍 PENCARIAN TIDAK HASIL",
                description=f"Tidak ada item yang cocok dengan '{keyword}'",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="⚠️ Error",
            description=f"Terjadi kesalahan saat memproses pencarian: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Command info item lengkap
@bot.command(name="iteminfo")
async def iteminfo(ctx, *, item_name: str):
    try:
        item_details = get_item_details(item_name)
        if item_details:
            tier_info = f"Tier {item_details['tier']}" if item_details.get('tier') else "Tier tidak diketahui"
            
            embed = discord.Embed(
                title=f"🔍 {item_details['name'].upper()}",
                description=f"**{tier_info}**\n🆔 ID: {item_details['id']}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📋 Recipe",
                value=f"```{item_details['recipe']}```" if item_details['recipe'] else "Tidak ada recipe",
                inline=False
            )
            
            embed.set_footer(text="Growtopia Recipe Bot • Info Lengkap")
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Item Tidak Ditemukan",
                description=f"Tidak ditemukan informasi untuk **{item_name}**",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="⚠️ Error",
            description=f"Terjadi kesalahan: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Command help
@bot.command(name="help")
async def help_command(ctx):
    # Buat embed dengan desain premium
    embed = discord.Embed(
        title="🌟 Growtopia Recipe Bot - Help Center",
        description="Selamat datang di sistem bantuan Growtopia Recipe Bot! Berikut adalah semua command yang tersedia:",
        color=discord.Color.gold()
    )
    
    # Tambahkan field untuk setiap kategori command
    embed.add_field(
        name="🔍 **PENCARIAN ITEM**",
        value="```css\n*recipe [nama_item] - Cari recipe item tertentu\n*search [keyword] - Cari item berdasarkan kata kunci\n*iteminfo [nama_item] - Info lengkap tentang item```",
        inline=False
    )
    
    embed.add_field(
        name="📊 **STATISTIK & INFO**",
        value="```fix\n*help - Menampilkan menu bantuan ini\n*stats - Statistik bot (coming soon)```",
        inline=False
    )
    
    # Informasi channel khusus dengan style premium
    target_channel = get_channel_mention(ALLOWED_CHANNELS[0])
    embed.add_field(
        name="📍 **CHANNEL KHUSUS**",
        value=f"╰┈➤ Bot ini hanya dapat digunakan di {target_channel}\n╰┈➤ [Link Langsung]({SPECIAL_CHANNEL_URL})",
        inline=False
    )
    
    # Footer dengan icon dan timestamp
    embed.set_footer(text="Growtopia Recipe Bot Premium • © 2024")
    
    await ctx.send(embed=embed)

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="❌ Command Tidak Ditemukan",
            description="Gunakan `*help` untuk melihat daftar command yang tersedia.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CheckFailure):
        # Jangan kirim pesan error untuk channel yang tidak diizinkan
        # karena sudah dikirim di channel_check
        pass
    else:
        embed = discord.Embed(
            title="⚠️ Terjadi Error",
            description=f"```{error}```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

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
