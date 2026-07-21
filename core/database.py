import sqlite3
import os


DB_PATH = "data/iris.db"



def get_connection():

    os.makedirs(
        "data",
        exist_ok=True
    )

    return sqlite3.connect(
        DB_PATH
    )



def add_column_if_missing(
    cursor,
    table,
    column,
    column_type
):

    cursor.execute(
        f"PRAGMA table_info({table})"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]


    if column not in columns:

        cursor.execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {column} {column_type}
            """
        )



def init_database():

    print("📦 Inicjalizacja bazy danych...")

    conn = get_connection()
    cursor = conn.cursor()



    # ==========================
    # SERWERY
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guilds (

        guild_id INTEGER PRIMARY KEY,

        log_channel INTEGER,

        welcome_channel INTEGER,

        prefix TEXT DEFAULT '!'

    )
    """)



    # dodatkowe kanały logów

    add_column_if_missing(
        cursor,
        "guilds",
        "member_log_channel",
        "INTEGER"
    )


    add_column_if_missing(
        cursor,
        "guilds",
        "moderation_log_channel",
        "INTEGER"
    )


    add_column_if_missing(
        cursor,
        "guilds",
        "message_log_channel",
        "INTEGER"
    )



    # ==========================
    # WARNY
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
    # USTAWIENIA MODERACJI
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
    # WHITELISTA AUTOMODA
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
    # ZAKAZANE SŁOWA
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bad_words (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        guild_id INTEGER,

        word TEXT

    )
    """)



    conn.commit()
    conn.close()


    print("✅ Baza danych gotowa")