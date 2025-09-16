import sqlite3
import os

DB_FILE = "growtopia_items.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        tier INTEGER,
        recipe TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_item(item_id, name, tier, recipe):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO items (id, name, tier, recipe) VALUES (?, ?, ?, ?)", 
              (item_id, name, tier, recipe))
    conn.commit()
    conn.close()

def get_recipe(item_name):
    """Mendapatkan recipe untuk item tertentu (case-insensitive)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Coba beberapa format pencarian
    attempts = [
        item_name,                  # Format asli
        item_name.title(),          # Title Case
        item_name.upper(),          # UPPERCASE
        item_name.lower(),          # lowercase
    ]
    
    for attempt in attempts:
        cursor.execute("SELECT recipe FROM items WHERE name = ?", (attempt,))
        result = cursor.fetchone()
        if result:
            conn.close()
            return result[0]
    
    # Jika masih tidak ketemu, coba dengan LIKE (partial match)
    cursor.execute("SELECT recipe FROM items WHERE LOWER(name) LIKE LOWER(?)", (f"%{item_name}%",))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else None

def get_all_items():
    """Mendapatkan semua items dari database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM items ORDER BY name")
    items = cursor.fetchall()
    conn.close()
    return items

def normalize_item_names():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Ambil semua item
    cursor.execute("SELECT id, name FROM items")
    items = cursor.fetchall()
    
    # Update nama menjadi Title Case untuk konsistensi
    for item_id, item_name in items:
        normalized_name = item_name.title()
        if normalized_name != item_name:
            cursor.execute("UPDATE items SET name = ? WHERE id = ?", 
                          (normalized_name, item_id))
            print(f"Updated: {item_name} -> {normalized_name}")
    
    conn.commit()
    conn.close()
    print("Database normalized successfully!")

if __name__ == "__main__":
    normalize_item_names()
