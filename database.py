import sqlite3
import os

DB_FILE = "growtopia_items.db"

def init_db():
    """Inisialisasi database dan buat tabel jika belum ada"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Buat tabel items
    c.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        tier INTEGER,
        recipe TEXT
    )
    """)
    
    # Verifikasi tabel berhasil dibuat
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
    result = c.fetchone()
    
    conn.commit()
    conn.close()
    
    if result:
        print(f"✅ Tabel 'items' berhasil dibuat/ditemukan di {DB_FILE}")
        return True
    else:
        print(f"❌ Gagal membuat tabel 'items' di {DB_FILE}")
        return False

def save_item(item_id, name, tier, recipe):
    """Menyimpan item ke database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO items (id, name, tier, recipe) VALUES (?, ?, ?, ?)", 
                 (item_id, name, tier, recipe))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error saving item {name}: {e}")
        return False
    finally:
        conn.close()

def get_recipe(item_name):
    """Mendapatkan recipe untuk item tertentu (case-insensitive)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Coba pencarian case-insensitive dengan LIKE
        cursor.execute("SELECT recipe FROM items WHERE LOWER(name) = LOWER(?)", (item_name,))
        result = cursor.fetchone()
        
        if not result:
            # Coba partial match jika exact match tidak ditemukan
            cursor.execute("SELECT recipe FROM items WHERE LOWER(name) LIKE LOWER(?)", (f"%{item_name}%",))
            result = cursor.fetchone()
        
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"❌ Error getting recipe for {item_name}: {e}")
        return None
    finally:
        conn.close()

def get_all_items():
    """Mendapatkan semua items dari database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name FROM items ORDER BY name")
        items = cursor.fetchall()
        return items
    except sqlite3.Error as e:
        print(f"❌ Error getting all items: {e}")
        return []
    finally:
        conn.close()

def normalize_item_names():
    """Normalisasi nama item ke Title Case"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Ambil semua item
        cursor.execute("SELECT id, name FROM items")
        items = cursor.fetchall()
        
        updated_count = 0
        for item_id, item_name in items:
            normalized_name = item_name.title()
            if normalized_name != item_name:
                cursor.execute("UPDATE items SET name = ? WHERE id = ?", 
                             (normalized_name, item_id))
                print(f"Updated: {item_name} -> {normalized_name}")
                updated_count += 1
        
        conn.commit()
        print(f"✅ Database normalized successfully! {updated_count} items updated.")
        return updated_count
    except sqlite3.Error as e:
        print(f"❌ Error normalizing database: {e}")
        return 0
    finally:
        conn.close()

def check_database():
    """Memeriksa status database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Periksa tabel yang ada
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"📊 Tabel dalam database: {tables}")
        
        # Periksa jumlah item
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        print(f"📦 Jumlah item dalam database: {count}")
        
        return True, count
    except sqlite3.Error as e:
        print(f"❌ Error checking database: {e}")
        return False, 0
    finally:
        conn.close()

def get_item_details(item_name):
    """Dapatkan detail lengkap item termasuk image_url"""
    conn = sqlite3.connect('items.db')
    c = conn.cursor()
    
    # Cari item dengan nama yang cocok (case-insensitive)
    c.execute("SELECT id, name, tier, recipe, image_url FROM items WHERE LOWER(name) = LOWER(?)", (item_name,))
    result = c.fetchone()
    
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'name': result[1],
            'tier': result[2],
            'recipe': result[3],
            'image_url': result[4]
        }
    return None

if __name__ == "__main__":
    # Inisialisasi database terlebih dahulu
    if init_db():
        normalize_item_names()
        check_database()

