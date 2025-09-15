import json
import os
from database import save_item, get_all_items

ITEMS_FILE = "items.json"  # file JSON contoh yang berisi semua item dan recipe

def fetch_and_parse_items():
    """
    Ambil items.json, parse, simpan ke DB, return list item baru
    """
    if not os.path.exists(ITEMS_FILE):
        print("❌ items.json tidak ditemukan!")
        return []

    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    old_items = {name for _, name in get_all_items()}
    new_items = []

    for item in data:
        item_id = item["id"]
        name = item["name"]
        recipe = item.get("recipe", "Tidak ada recipe")
        save_item(item_id, name, recipe)

        if name not in old_items:
            new_items.append(item)

    return new_items
