import datetime
import time

import discord
from discord.ext import commands

from core.base_cog import BaseCog
from database.database import get_connection


class AutoMod(BaseCog):

    SPAM_INTERVAL = 5
    SPAM_LIMIT = 5
    TIMEOUT_MINUTES = 2

    BLOCKED_LINKS = (
        "http://",
        "https://",
        "www.",
        "discord.gg/",
    )

    def __init__(self, bot):
        super().__init__(bot)
        self.message_cache: dict[tuple[int, int], list[float]] = {}

    async def get_settings(
        self,
        guild_id: int,
    ) -> tuple[int, int, int]:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT anti_spam,
                   anti_links,
                   anti_caps
            FROM automod_settings
            WHERE guild_id = ?
            """,
            (guild_id,),
        )

        data = cursor.fetchone()

        conn.close()

        return data if data else (1, 1, 1)

    async def add_warn(
        self,
        guild: discord.Guild,
        user: discord.Member,
        reason: str,
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO warnings
            (
                guild_id,
                user_id,
                moderator_id,
                reason
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                guild.id,
                user.id,
                self.bot.user.id,
                reason,
            ),
        )

        conn.commit()
        conn.close()

        self.logger.info(
            f"AutoMod -> {user} | {reason}"
        )

    async def timeout_user(
        self,
        member: discord.Member,
    ):

        until = (
            datetime.datetime.now(
                datetime.timezone.utc
            )
            +
            datetime.timedelta(
                minutes=self.TIMEOUT_MINUTES
            )
        )

        try:

            await member.timeout(
                until,
                reason="Iris AutoMod",
            )

        except Exception as error:
            self.logger.exception(error)

    async def is_whitelisted(
        self,
        message: discord.Message,
    ) -> bool:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT user_id,
                   role_id
            FROM automod_whitelist
            WHERE guild_id = ?
            """,
            (message.guild.id,),
        )

        rows = cursor.fetchall()

        conn.close()

        for user_id, role_id in rows:

            if user_id == message.author.id:
                return True

            if role_id and any(
                role.id == role_id
                for role in message.author.roles
            ):
                return True

        return False

    async def contains_bad_word(
        self,
        message: discord.Message,
    ) -> bool:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT word
            FROM bad_words
            WHERE guild_id = ?
            """,
            (message.guild.id,),
        )

        words = cursor.fetchall()

        conn.close()

        content = message.content.lower()

        return any(
            word.lower() in content
            for (word,) in words
        )

    async def delete_and_warn(
        self,
        message: discord.Message,
        reason: str,
        notify: str,
        timeout: bool = False,
    ):

        try:

            await message.delete()

            await self.add_warn(
                message.guild,
                message.author,
                reason,
            )

            if timeout:
                await self.timeout_user(
                    message.author
                )

            await message.channel.send(
                f"⚠️ {message.author.mention}\n{notify}",
                delete_after=5,
            )

        except Exception as error:
            self.logger.exception(error)

    def spam_detected(
        self,
        message: discord.Message,
    ) -> bool:

        key = (
            message.guild.id,
            message.author.id,
        )

        now = time.time()

        messages = self.message_cache.get(
            key,
            [],
        )

        messages.append(now)

        messages = [
            value
            for value in messages
            if now - value < self.SPAM_INTERVAL
        ]

        self.message_cache[key] = messages

        return len(messages) >= self.SPAM_LIMIT

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message,
    ):

        if not message.guild:
            return

        if message.author.bot:
            return

        if message.author.guild_permissions.administrator:
            return

        if await self.is_whitelisted(message):
            return

        anti_spam, anti_links, anti_caps = (
            await self.get_settings(
                message.guild.id
            )
        )

        content = message.content.lower()

        # BLACKLIST

        if await self.contains_bad_word(message):

            await self.delete_and_warn(
                message,
                "AutoMod: Zakazane słowo",
                "Zakazane słowo.",
            )

            return

        # SPAM

        if anti_spam and self.spam_detected(message):

            try:

                await message.channel.purge(
                    limit=self.SPAM_LIMIT,
                    check=lambda m:
                    m.author.id == message.author.id,
                )

            except Exception as error:
                self.logger.exception(error)

            await self.add_warn(
                message.guild,
                message.author,
                "AutoMod: Spam",
            )

            await self.timeout_user(
                message.author,
            )

            self.message_cache[
                (
                    message.guild.id,
                    message.author.id,
                )
            ] = []

            await message.channel.send(
                f"⚠️ {message.author.mention}\n"
                "Spam wykryty.\n"
                "+1 warn + timeout 2 min.",
                delete_after=5,
            )

            return

        # LINKI

        if anti_links:

            if any(
                link in content
                for link in self.BLOCKED_LINKS
            ):

                await self.delete_and_warn(
                    message,
                    "AutoMod: Link",
                    "Linki są zablokowane.",
                )

                return

        # CAPS

        if anti_caps:

            letters = [
                letter
                for letter in message.content
                if letter.isalpha()
            ]

            if len(letters) >= 10:

                upper = sum(
                    letter.isupper()
                    for letter in letters
                )

                if upper / len(letters) >= 0.7:

                    await self.delete_and_warn(
                        message,
                        "AutoMod: Caps",
                        "Nie pisz całych wiadomości CAPSLOCKIEM.",
                    )


async def setup(bot):
    await bot.add_cog(
        AutoMod(bot)
    )