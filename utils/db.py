import sqlite3
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "app.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'User'
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activities(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        item_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        meta TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ratings(
        user_id INTEGER,
        item_id INTEGER,
        rating INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, item_id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bandit(
        algorithm TEXT PRIMARY KEY,
        plays INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

def ensure_default_users():
    conn = get_conn()
    cur = conn.cursor()
    # Check if any user exists
    cur.execute("SELECT COUNT(*) as c FROM users")
    if cur.fetchone()["c"] == 0:
        # Insert default users (passwords: admin123, analyst123, user123)
        cur.execute("INSERT OR IGNORE INTO users(email, password_hash, role) VALUES(?,?,?)",
                    ("admin@demo.com", "TO_SET_ADMIN", "Admin"))
        cur.execute("INSERT OR IGNORE INTO users(email, password_hash, role) VALUES(?,?,?)",
                    ("analyst@demo.com", "TO_SET_ANALYST", "Analyst"))
        cur.execute("INSERT OR IGNORE INTO users(email, password_hash, role) VALUES(?,?,?)",
                    ("user@demo.com", "TO_SET_USER", "User"))
        conn.commit()
    conn.close()

def set_password(email: str, password_hash: str):
    conn = get_conn()
    conn.execute("UPDATE users SET password_hash=? WHERE email=?", (password_hash, email))
    conn.commit()
    conn.close()

def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    return row

def insert_user(email: str, password_hash: str, role: str = "User") -> Tuple[bool, Optional[str]]:
    try:
        conn = get_conn()
        conn.execute("INSERT INTO users(email, password_hash, role) VALUES(?,?,?)",
                     (email, password_hash, role))
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def log_activity(user_id: int, type_: str, item_id: Optional[int] = None, meta: str = ""):
    conn = get_conn()
    conn.execute("INSERT INTO activities(user_id, type, item_id, meta) VALUES(?,?,?,?)",
                 (user_id, type_, item_id, meta))
    conn.commit()
    conn.close()

def rate_item(user_id: int, item_id: int, rating: int):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO ratings(user_id, item_id, rating) VALUES(?,?,?)",
                 (user_id, item_id, rating))
    conn.commit()
    conn.close()

def fetch_user_events() -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities ORDER BY timestamp DESC LIMIT 1000")
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_ratings() -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ratings")
    rows = cur.fetchall()
    conn.close()
    return rows

def bandit_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bandit")
    rows = cur.fetchall()
    conn.close()
    return rows

def bandit_update(algorithm: str, won: bool):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO bandit(algorithm, plays, wins) VALUES(?, 0, 0)", (algorithm,))
    cur.execute("UPDATE bandit SET plays = plays + 1, wins = wins + ? WHERE algorithm=?", (1 if won else 0, algorithm))
    conn.commit()
    conn.close()
