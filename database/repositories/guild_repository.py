from database.repositories.base_repository import BaseRepository


class GuildRepository(BaseRepository):

    def create_guild(self, guild_id: int):

        self.cursor.execute(
            """
            INSERT OR IGNORE INTO guilds(guild_id)
            VALUES(?)
            """,
            (guild_id,),
        )

        self.commit()

    def get_prefix(self, guild_id: int):

        self.cursor.execute(
            """
            SELECT prefix
            FROM guilds
            WHERE guild_id = ?
            """,
            (guild_id,),
        )

        row = self.cursor.fetchone()

        if row:
            return row[0]

        return "!"

    def set_prefix(
        self,
        guild_id: int,
        prefix: str,
    ):

        self.cursor.execute(
            """
            UPDATE guilds
            SET prefix = ?
            WHERE guild_id = ?
            """,
            (
                prefix,
                guild_id,
            ),
        )

        self.commit()

    def set_log_channel(
        self,
        guild_id: int,
        channel_id: int,
    ):

        self.cursor.execute(
            """
            UPDATE guilds
            SET log_channel = ?
            WHERE guild_id = ?
            """,
            (
                channel_id,
                guild_id,
            ),
        )

        self.commit()