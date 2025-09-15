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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM items")
    items = c.fetchall()
    conn.close()
    return items
