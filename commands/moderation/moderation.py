import datetime

import discord

from core.base_cog import BaseCog
from database.database import get_connection


class Warnings(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)

    @discord.app_commands.command(
        name="warn",
        description="Nadaje użytkownikowi ostrzeżenie"
    )
    @discord.app_commands.describe(
        member="Użytkownik",
        reason="Powód ostrzeżenia"
    )
    @discord.app_commands.checks.has_permissions(
        manage_messages=True
    )
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Brak powodu"
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO warnings
            (guild_id, user_id, moderator_id, reason)
            VALUES (?, ?, ?, ?)
            """,
            (
                interaction.guild.id,
                member.id,
                interaction.user.id,
                reason,
            ),
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                interaction.guild.id,
                member.id,
            ),
        )

        warns = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                timeout_warns,
                kick_warns,
                ban_warns
            FROM moderation_settings
            WHERE guild_id = ?
            """,
            (
                interaction.guild.id,
            ),
        )

        settings = cursor.fetchone() or (3, 5, 10)

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="⚠️ Ostrzeżenie",
            color=discord.Color.yellow(),
        )

        embed.add_field(
            name="Użytkownik",
            value=member.mention,
        )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
        )

        embed.add_field(
            name="Powód",
            value=reason,
            inline=False,
        )

        embed.add_field(
            name="Liczba ostrzeżeń",
            value=str(warns),
        )

        await interaction.response.send_message(
            embed=embed
        )

        self.logger.info(
            f"{interaction.user} ostrzegł {member} ({reason})"
        )

        timeout_warns, kick_warns, ban_warns = settings

        try:

            if warns >= ban_warns:

                await member.ban(
                    reason="Iris: limit ostrzeżeń"
                )

                await interaction.followup.send(
                    f"🔨 {member.mention} został zbanowany."
                )

            elif warns >= kick_warns:

                await member.kick(
                    reason="Iris: limit ostrzeżeń"
                )

                await interaction.followup.send(
                    f"👢 {member.mention} został wyrzucony."
                )

            elif warns >= timeout_warns:

                until = (
                    datetime.datetime.now(
                        datetime.timezone.utc
                    )
                    +
                    datetime.timedelta(
                        minutes=10
                    )
                )

                await member.timeout(
                    until,
                    reason="Iris: limit ostrzeżeń"
                )

                await interaction.followup.send(
                    f"🔇 {member.mention} otrzymał timeout."
                )

        except Exception as error:

            self.logger.exception(error)

    @discord.app_commands.command(
        name="warnlist",
        description="Pokazuje ostrzeżenia użytkownika"
    )
    async def warnlist(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT reason, date
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            ORDER BY id DESC
            """,
            (
                interaction.guild.id,
                member.id,
            ),
        )

        data = cursor.fetchall()

        conn.close()

        if not data:

            await interaction.response.send_message(
                "✅ Ten użytkownik nie posiada ostrzeżeń."
            )

            return

        description = ""

        for index, (reason, date) in enumerate(
            data,
            start=1,
        ):
            description += (
                f"**{index}.** {reason}\n"
                f"📅 {date}\n\n"
            )

        embed = discord.Embed(
            title=f"⚠️ Ostrzeżenia {member}",
            description=description[:4000],
            color=discord.Color.orange(),
        )

        await interaction.response.send_message(
            embed=embed
        )

    @discord.app_commands.command(
        name="clearwarns",
        description="Usuwa wszystkie ostrzeżenia użytkownika"
    )
    @discord.app_commands.checks.has_permissions(
        manage_messages=True
    )
    async def clearwarns(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                interaction.guild.id,
                member.id,
            ),
        )

        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"🧹 Usunięto **{deleted}** ostrzeżeń użytkownika {member.mention}."
        )

        self.logger.info(
            f"{interaction.user} usunął ostrzeżenia użytkownika {member}"
        )


async def setup(bot):
    await bot.add_cog(Warnings(bot))