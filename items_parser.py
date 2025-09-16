import json
import os
from database import save_item, get_all_items

ITEMS_FILE = "items.json"

def fetch_and_parse_items():
    """
    Ambil items.json, parse, simpan ke DB, return list item baru
    """
    if not os.path.exists(ITEMS_FILE):
        print("❌ items.json tidak ditemukan!")
        return []

    try:
        with open(ITEMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading items.json: {e}")
        return []

    # Dapatkan daftar item yang sudah ada di database
    existing_items = {name.lower() for _, name in get_all_items()}
    new_items = []

    for item in data:
        try:
            item_id = item["id"]
            name = item["name"]
            tier = item.get("tier", 0)
            recipe = item.get("recipe", "Tidak ada recipe")
            
            # Simpan item ke database
            save_item(item_id, name, tier, recipe)
            
            # Cek jika item baru
            if name.lower() not in existing_items:
                new_items.append({
                    "id": item_id,
                    "name": name,
                    "tier": tier,
                    "recipe": recipe
                })
        except KeyError as e:
            print(f"❌ Error processing item: Missing key {e} in item {item}")
        except Exception as e:
            print(f"❌ Error processing item {item.get('name', 'unknown')}: {e}")

    print(f"✅ Loaded {len(data)} items, {len(new_items)} new items")
    return new_items

def load_all_items():
    """Memuat semua item dari JSON ke database"""
    if not os.path.exists(ITEMS_FILE):
        print("❌ items.json tidak ditemukan!")
        return False

    try:
        with open(ITEMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading items.json: {e}")
        return False

    success_count = 0
    for item in data:
        try:
            item_id = item["id"]
            name = item["name"]
            tier = item.get("tier", 0)
            recipe = item.get("recipe", "Tidak ada recipe")
            
            if save_item(item_id, name, tier, recipe):
                success_count += 1
        except Exception as e:
            print(f"❌ Error saving item {item.get('name', 'unknown')}: {e}")

    print(f"✅ Successfully loaded {success_count} items to database")
    return success_count > 0

if __name__ == "__main__":
    # Jalankan ini untuk memuat semua item ke database
    from database import init_db
    init_db()
    load_all_items()
