import os
import sqlite3
from pathlib import Path
from core.logger import get_logger

logger = get_logger(__name__)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "iris.db"

def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)

def add_column_if_missing(cursor: sqlite3.Cursor, table: str, column: str, column_type: str) -> None:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        logger.info(f"Adding column '{column}' to table '{table}'")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

def init_database() -> sqlite3.Connection:
    logger.info("Initializing database...")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guilds (
        guild_id INTEGER PRIMARY KEY,
        log_channel INTEGER,
        welcome_channel INTEGER,
        prefix TEXT DEFAULT '/'
    )
    """)

    add_column_if_missing(cursor, "guilds", "member_log_channel", "INTEGER")
    add_column_if_missing(cursor, "guilds", "moderation_log_channel", "INTEGER")
    add_column_if_missing(cursor, "guilds", "message_log_channel", "INTEGER")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        user_id INTEGER,
        moderator_id INTEGER,
        reason TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS moderation_settings (
        guild_id INTEGER PRIMARY KEY,
        timeout_warns INTEGER DEFAULT 3,
        kick_warns INTEGER DEFAULT 5,
        ban_warns INTEGER DEFAULT 10
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS automod_settings (
        guild_id INTEGER PRIMARY KEY,
        anti_spam INTEGER DEFAULT 1,
        anti_links INTEGER DEFAULT 1,
        anti_caps INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS automod_whitelist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        user_id INTEGER,
        role_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bad_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        word TEXT
    )
    """)

    # --- SYSTEM TICKETÓW ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_settings (
        guild_id INTEGER PRIMARY KEY,
        category_id INTEGER,
        support_role_id INTEGER,
        counter INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        channel_id INTEGER,
        user_id INTEGER,
        status TEXT DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ==========================
    # TEMP ROLES
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS temp_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        user_id INTEGER,
        role_id INTEGER,
        expires_at TIMESTAMP
    )
    """)

    conn.commit()
    logger.info("Database initialized successfully.")
    return conn