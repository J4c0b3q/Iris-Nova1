from database.repositories.base_repository import BaseRepository


class WarningRepository(BaseRepository):

    def add_warning(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
    ):

        self.cursor.execute(
            """
            INSERT INTO warnings(
                guild_id,
                user_id,
                moderator_id,
                reason
            )
            VALUES(?,?,?,?)
            """,
            (
                guild_id,
                user_id,
                moderator_id,
                reason,
            ),
        )

        self.commit()

    def get_warning_count(
        self,
        guild_id: int,
        user_id: int,
    ):

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                guild_id,
                user_id,
            ),
        )

        return self.cursor.fetchone()[0]