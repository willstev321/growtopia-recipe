from database import init_db, update_db_schema, get_all_items, save_item
from items_parser import fetch_and_parse_items
import json

def update_existing_database():
    """Memperbarui database yang sudah ada dengan menambahkan image_url"""
    print("🔄 Memperbarui database yang sudah ada...")
    
    # Inisialisasi database
    init_db()
    update_db_schema()
    
    # Baca items.json
    try:
        with open("items.json", "r", encoding="utf-8") as f:
            items_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading items.json: {e}")
        return
    
    # Buat mapping dari nama item ke image_url
    image_mapping = {item['name'].lower(): item.get('image_url') for item in items_data}
    
    # Dapatkan semua item dari database
    existing_items = get_all_items()
    
    # Perbarui setiap item dengan image_url
    updated_count = 0
    for item_id, item_name in existing_items:
        image_url = image_mapping.get(item_name.lower())
        if image_url:
            # Simpan kembali item dengan image_url
            # Untuk mendapatkan tier dan recipe, kita perlu query database lagi
            # atau menggunakan data dari items.json
            for item_data in items_data:
                if item_data['name'].lower() == item_name.lower():
                    save_item(
                        item_data['id'],
                        item_data['name'],
                        item_data.get('tier', 0),
                        item_data.get('recipe', 'Tidak ada recipe'),
                        image_url
                    )
                    updated_count += 1
                    break
    
    print(f"✅ Database updated! {updated_count} items diperbarui dengan image_url.")

if __name__ == "__main__":
    update_existing_database()
