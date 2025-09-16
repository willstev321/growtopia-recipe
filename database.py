import sqlite3
import os

DB_FILE = "growtopia_items.db"

def init_db():
    """Inisialisasi database dan buat tabel jika belum ada"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Buat tabel items dengan kolom tier
    c.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        tier INTEGER,
        recipe TEXT
    )
    """)
    
    # Buat index untuk pencarian case-insensitive
    c.execute("CREATE INDEX IF NOT EXISTS idx_items_lower_name ON items(LOWER(name))")
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_FILE}")

def save_item(item_id, name, tier, recipe):
    """Menyimpan item ke database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT OR REPLACE INTO items (id, name, tier, recipe) VALUES (?, ?, ?, ?)", 
            (item_id, name, tier, recipe)
        )
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
    c = conn.cursor()
    
    try:
        # Pencarian case-insensitive
        c.execute("SELECT recipe FROM items WHERE LOWER(name) = LOWER(?)", (item_name,))
        result = c.fetchone()
        
        if not result:
            # Coba partial match jika exact match tidak ditemukan
            c.execute("SELECT recipe FROM items WHERE LOWER(name) LIKE LOWER(?)", (f"%{item_name}%",))
            result = c.fetchone()
        
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"❌ Error getting recipe for {item_name}: {e}")
        return None
    finally:
        conn.close()

def get_all_items():
    """Mendapatkan semua items dari database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute("SELECT id, name FROM items ORDER BY name")
        items = c.fetchall()
        return items
    except sqlite3.Error as e:
        print(f"❌ Error getting all items: {e}")
        return []
    finally:
        conn.close()

def get_item_details(item_name):
    """Mendapatkan detail lengkap item (case-insensitive)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute("SELECT id, name, tier, recipe FROM items WHERE LOWER(name) = LOWER(?)", (item_name,))
        result = c.fetchone()
        
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "tier": result[2],
                "recipe": result[3]
            }
        return None
    except sqlite3.Error as e:
        print(f"❌ Error getting item details for {item_name}: {e}")
        return None
    finally:
        conn.close()

def search_items(keyword):
    """Mencari item berdasarkan keyword (case-insensitive)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute("SELECT id, name FROM items WHERE LOWER(name) LIKE LOWER(?) ORDER BY name", (f"%{keyword}%",))
        items = c.fetchall()
        return items
    except sqlite3.Error as e:
        print(f"❌ Error searching items: {e}")
        return []
    finally:
        conn.close()
