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

    conn = get_connection()
    cursor = conn.cursor()



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guilds (

        guild_id INTEGER PRIMARY KEY,

        log_channel INTEGER,

        welcome_channel INTEGER,

        prefix TEXT DEFAULT '!'

    )
    """)



    # nowe kanały logów

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



    conn.commit()
    conn.close()