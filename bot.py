import discord
from discord.ext import commands, tasks
import os
from items_parser import fetch_and_parse_items
from database import init_db, get_recipe, get_all_items

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

# Inisialisasi DB
init_db()

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
                channel = discord.utils.get(guild.text_channels, name="growtopia-news")
                if channel:
                    for item in new_items:
                        await channel.send(
                            f"🆕 Item baru: **{item['name']}** (Tier {item['tier']})\n"
                            f"Recipe: {item.get('recipe','Tidak ada')}"
                        )
                    break
    except Exception as e:
        print(f"❌ Error in check_items_update: {e}")

# Command lihat recipe
@bot.command(name="recipe")
async def recipe(ctx, *, item_name: str):
    try:
        recipe_text = get_recipe(item_name)
        if recipe_text:
            await ctx.send(f"📦 Recipe untuk **{item_name}**:\n{recipe_text}")
        else:
            await ctx.send(f"❌ Tidak ada recipe untuk '{item_name}'")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# Command cari item
@bot.command(name="search")
async def search(ctx, *, keyword: str):
    try:
        items = get_all_items()
        # Gunakan lower() untuk pencarian case-insensitive
        results = [name for _, name in items if keyword.lower() in name.lower()]
        
        if results:
            limited_results = results[:10]  # Batasi hasil
            await ctx.send(
                f"🔍 Ditemukan {len(results)} item (menampilkan 10 pertama):\n" +
                "\n".join(f"• {item}" for item in limited_results)
            )
        else:
            await ctx.send(f"❌ Tidak ada item yang cocok dengan '{keyword}'")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            "❌ Command tidak ditemukan. Gunakan `?recipe [nama_item]` atau `?search [keyword]`"
        )
    else:
        await ctx.send(f"❌ Terjadi error: {error}")

# Jalankan bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        print("❌ ERROR: DISCORD_BOT_TOKEN tidak ditemukan di environment variables!")
        print("💡 Pastikan file .env ada dan berisi: DISCORD_BOT_TOKEN=your_token_here")
        exit(1)

    print("🚀 Starting bot...")
    bot.run(token)
