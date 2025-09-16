import discord
from discord.ext import commands, tasks
import os
from items_parser import fetch_and_parse_items
from database import init_db, get_recipe

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

# Inisialisasi DB
init_db()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_items_update.start()

# Background task untuk cek item baru
@tasks.loop(hours=24)
async def check_items_update():
    new_items = fetch_and_parse_items()
    if new_items:
        print(f"🆕 {len(new_items)} item baru ditemukan!")
        # Ubah 'growtopia-news' dengan nama channel Discord kamu
        channel = discord.utils.get(bot.get_all_channels(), name="growtopia-news")
        if channel:
            for item in new_items:
                await channel.send(f"🆕 Item baru: **{item['name']}** (ID {item['id']})\nRecipe: {item.get('recipe','Tidak ada')}")

# Command lihat recipe
@bot.command(name="recipe")
async def recipe(ctx, *, item_name: str):
    recipe_text = get_recipe(item_name)
    if recipe_text:
        await ctx.send(f"📦 Recipe untuk **{item_name}**:\n{recipe_text}")
    else:
        await ctx.send(f"❌ Tidak ada recipe untuk {item_name}")

# Command cari item
@bot.command(name="search")
async def search(ctx, *, keyword: str):
    from database import get_all_items
    items = get_all_items()
    results = [name for _, name in items if keyword.lower() in name.lower()]
    if results:
        await ctx.send(f"🔍 Item ditemukan:\n" + "\n".join(results))
    else:
        await ctx.send(f"❌ Tidak ada item yang cocok dengan '{keyword}'")

# Jalankan bot
token = os.getenv("DISCORD_BOT_TOKEN")

if not token:
    print("❌ Token tidak ditemukan! Pastikan sudah set di Environment Variables server.")
    exit(1)

bot.run(token)
