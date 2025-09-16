import discord
from discord.ext import commands, tasks
import os
import asyncio
from database import init_db, get_recipe, get_all_items, check_database

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"👥 Connected to {len(bot.guilds)} guild(s)")
    
    # Periksa status database
    db_ok, item_count = check_database()
    if not db_ok or item_count == 0:
        print("⚠️  Database kosong atau bermasalah. Pastikan items_parser.py dijalankan terlebih dahulu!")
    
    # Start background task
    check_items_update.start()

# Background task untuk cek item baru
@tasks.loop(hours=24)
async def check_items_update():
    try:
        # Import di sini untuk menghindari circular imports
        from items_parser import fetch_and_parse_items
        
        new_items = fetch_and_parse_items()
        if new_items:
            print(f"🆕 {len(new_items)} item baru ditemukan!")
            for guild in bot.guilds:
                channel = discord.utils.get(guild.text_channels, name="growtopia-news")
                if channel:
                    for item in new_items:
                        await channel.send(
                            f"🆕 Item baru: **{item['name']}** (Tier {item.get('tier', 'N/A')})\n"
                            f"Recipe: {item.get('recipe','Tidak ada')}"
                        )
                    break
    except Exception as e:
        print(f"❌ Error in check_items_update: {e}")

@check_items_update.before_loop
async def before_check_items():
    """Tunggu sampai bot siap sebelum menjalankan task"""
    await bot.wait_until_ready()

# Command lihat recipe
@bot.command(name="recipe")
async def recipe(ctx, *, item_name: str):
    try:
        recipe_text = get_recipe(item_name)
        if recipe_text:
            await ctx.send(f"📦 Recipe untuk **{item_name}**:\n{recipe_text}")
        else:
            # Coba suggestion
            items = get_all_items()
            suggestions = [name for _, name in items if item_name.lower() in name.lower()]
            
            if suggestions:
                suggestion_text = "\n".join(f"• {s}" for s in suggestions[:5])
                await ctx.send(
                    f"❌ Tidak ada recipe untuk '{item_name}'\n"
                    f"💡 Mungkin maksud Anda:\n{suggestion_text}"
                )
            else:
                await ctx.send(f"❌ Tidak ada recipe untuk '{item_name}'")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# Command cari item
@bot.command(name="search")
async def search(ctx, *, keyword: str):
    try:
        items = get_all_items()
        results = [name for _, name in items if keyword.lower() in name.lower()]
        
        if results:
            limited_results = results[:10]
            await ctx.send(
                f"🔍 Ditemukan {len(results)} item (menampilkan 10 pertama):\n" +
                "\n".join(f"• {item}" for item in limited_results)
            )
        else:
            await ctx.send(f"❌ Tidak ada item yang cocok dengan '{keyword}'")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# Command info database
@bot.command(name="dbinfo")
async def dbinfo(ctx):
    """Menampilkan informasi database"""
    try:
        db_ok, item_count = check_database()
        if db_ok:
            await ctx.send(f"📊 Status Database: ✅\n📦 Jumlah Item: {item_count}")
        else:
            await ctx.send("❌ Database bermasalah! Jalankan items_parser.py terlebih dahulu.")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            "❌ Command tidak ditemukan. Gunakan:\n"
            "• `?recipe [nama_item]` - Cari recipe\n"
            "• `?search [keyword]` - Cari item\n"
            "• `?dbinfo` - Info database"
        )
    else:
        await ctx.send(f"❌ Terjadi error: {error}")

# Jalankan bot
if __name__ == "__main__":
    # Inisialisasi database pertama kali
    if not init_db():
        print("❌ Gagal menginisialisasi database!")
        exit(1)
    
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_BOT_TOKEN tidak ditemukan!")
        print("💡 Pastikan file .env ada dan berisi: DISCORD_BOT_TOKEN=your_token_here")
        exit(1)

    print("🚀 Starting bot...")
    bot.run(token)
