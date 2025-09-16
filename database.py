import sqlite3
import json
import os

def init_db():
    """Inisialisasi database dengan tabel items"""
    conn = sqlite3.connect('items.db')
    c = conn.cursor()
    
    # Buat tabel jika belum ada
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id INTEGER PRIMARY KEY, 
                  name TEXT, 
                  tier INTEGER,
                  recipe TEXT,
                  image_url TEXT)''')
    
    conn.commit()
    conn.close()

def load_all_items():
    """Load semua items dari items.json ke database"""
    try:
        with open('items.json', 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        conn = sqlite3.connect('items.db')
        c = conn.cursor()
        
        # Kosongkan tabel sebelum mengisi ulang
        c.execute("DELETE FROM items")
        
        # Masukkan items ke database
        for item in items:
            c.execute("INSERT INTO items (id, name, tier, recipe, image_url) VALUES (?, ?, ?, ?, ?)",
                     (item['id'], item['name'], item.get('tier', 0), item.get('recipe', ''), item.get('image_url', '')))
        
        conn.commit()
        conn.close()
        print(f"✅ {len(items)} items berhasil dimuat ke database")
    except Exception as e:
        print(f"❌ Error loading items: {e}")

def get_recipe(item_name):
    """Dapatkan recipe untuk item tertentu"""
    conn = sqlite3.connect('items.db')
    c = conn.cursor()
    
    # Cari item dengan nama yang cocok (case-insensitive)
    c.execute("SELECT recipe FROM items WHERE LOWER(name) = LOWER(?)", (item_name,))
    result = c.fetchone()
    
    conn.close()
    return result[0] if result else None

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

def get_all_items():
    """Dapatkan semua items dari database"""
    conn = sqlite3.connect('items.db')
    c = conn.cursor()
    
    c.execute("SELECT id, name FROM items")
    items = c.fetchall()
    
    conn.close()
    return items

def search_items(keyword):
    """Cari items berdasarkan keyword"""
    conn = sqlite3.connect('items.db')
    c = conn.cursor()
    
    # Cari item dengan nama yang mengandung keyword (case-insensitive)
    c.execute("SELECT id, name FROM items WHERE LOWER(name) LIKE LOWER(?)", ('%' + keyword + '%',))
    items = c.fetchall()
    
    conn.close()
    return items

def get_item_image_url(item_name):
    """Dapatkan URL gambar untuk item tertentu"""
    conn = sqlite3.connect('items.db')
    c = conn.cursor()
    
    # Cari item dengan nama yang cocok (case-insensitive)
    c.execute("SELECT image_url FROM items WHERE LOWER(name) = LOWER(?)", (item_name,))
    result = c.fetchone()
    
    conn.close()
    return result[0] if result else None

# Tambahkan fungsi save_item yang diperlukan oleh items_parser.py
def save_item(item_id, name, tier, recipe, image_url=None):
    """Simpan atau update item ke database"""
    conn = sqlite3.connect('items.db')
    c = conn.cursor()
    
    # Cek apakah item sudah ada
    c.execute("SELECT id FROM items WHERE id = ?", (item_id,))
    exists = c.fetchone()
    
    if exists:
        # Update item yang sudah ada
        c.execute("UPDATE items SET name = ?, tier = ?, recipe = ?, image_url = ? WHERE id = ?",
                 (name, tier, recipe, image_url, item_id))
    else:
        # Insert item baru
        c.execute("INSERT INTO items (id, name, tier, recipe, image_url) VALUES (?, ?, ?, ?, ?)",
                 (item_id, name, tier, recipe, image_url))
    
    conn.commit()
    conn.close()
