import sqlite3
import time
import os

DB_PATH = "database/kevin_memory.db"

def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_description TEXT,
            status TEXT DEFAULT 'pending',
            created_at REAL,
            completed_at REAL
        )
    ''')
    
    # State table (for strict mode and current focus)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Conversation history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp REAL
        )
    ''')
    
    conn.commit()
    conn.close()

_init_db()

def add_task(description: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (task_description, created_at) VALUES (?, ?)", (description, time.time()))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_pending_tasks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_description, created_at FROM tasks WHERE status='pending'")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def complete_task(task_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status='completed', completed_at=? WHERE id=?", (time.time(), task_id))
    conn.commit()
    conn.close()

def log_conversation(role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversation (role, content, timestamp) VALUES (?, ?, ?)", (role, content, time.time()))
    conn.commit()
    conn.close()

def set_state(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_state(key: str, default=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM state WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default
