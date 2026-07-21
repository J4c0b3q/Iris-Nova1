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


def add_column_if_missing(
    cursor: sqlite3.Cursor,
    table: str,
    column: str,
    column_type: str,
) -> None:

    cursor.execute(f"PRAGMA table_info({table})")

    columns = [row[1] for row in cursor.fetchall()]

    if column not in columns:
        logger.info(f"Adding column '{column}' to table '{table}'")

        cursor.execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {column} {column_type}
            """
        )


def init_database() -> sqlite3.Connection:

    logger.info("Initializing database...")

    conn = get_connection()
    cursor = conn.cursor()

    # ==========================
    # GUILDS
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guilds (

        guild_id INTEGER PRIMARY KEY,

        log_channel INTEGER,

        welcome_channel INTEGER,

        prefix TEXT DEFAULT '!'

    )
    """)

    add_column_if_missing(
        cursor,
        "guilds",
        "member_log_channel",
        "INTEGER",
    )

    add_column_if_missing(
        cursor,
        "guilds",
        "moderation_log_channel",
        "INTEGER",
    )

    add_column_if_missing(
        cursor,
        "guilds",
        "message_log_channel",
        "INTEGER",
    )

    # ==========================
    # WARNINGS
    # ==========================

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

    # ==========================
    # MODERATION
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS moderation_settings (

        guild_id INTEGER PRIMARY KEY,

        timeout_warns INTEGER DEFAULT 3,

        kick_warns INTEGER DEFAULT 5,

        ban_warns INTEGER DEFAULT 10

    )
    """)

    # ==========================
    # AUTOMOD
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS automod_settings (

        guild_id INTEGER PRIMARY KEY,

        anti_spam INTEGER DEFAULT 1,

        anti_links INTEGER DEFAULT 1,

        anti_caps INTEGER DEFAULT 1

    )
    """)

    # ==========================
    # AUTOMOD WHITELIST
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS automod_whitelist (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        guild_id INTEGER,

        user_id INTEGER,

        role_id INTEGER

    )
    """)

    # ==========================
    # BAD WORDS
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bad_words (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        guild_id INTEGER,

        word TEXT

    )
    """)

    conn.commit()

    logger.info("Database initialized successfully.")

    return conn