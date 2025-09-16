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
        recipe TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_item(item_id, name, recipe):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO items (id, name, recipe) VALUES (?, ?, ?)", (item_id, name, recipe))
    conn.commit()
    conn.close()

def get_recipe(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT recipe FROM items WHERE name LIKE ?", (f"%{name}%",))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_items():
    """Mendapatkan semua items dari database"""
    conn = sqlite3.connect('growtopia.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM items ORDER BY name")
    items = cursor.fetchall()
    conn.close()
    return items

def get_recipe(item_name):
    """Mendapatkan recipe untuk item tertentu (case-insensitive)"""
    conn = sqlite3.connect('growtopia.db')
    cursor = conn.cursor()
    
    # Gunakan LOWER() untuk pencarian case-insensitive
    cursor.execute("SELECT recipe FROM items WHERE LOWER(name) = LOWER(?)", (item_name,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else None

def normalize_item_names():
    conn = sqlite3.connect('growtopia.db')
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

def get_recipe_robust(item_name):
    """Pencarian yang lebih robust dengan multiple attempts"""
    conn = sqlite3.connect('growtopia.db')
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
    cursor.execute("SELECT recipe FROM items WHERE name LIKE ?", (f"%{item_name}%",))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else None

if __name__ == "__main__":
    normalize_item_names()

