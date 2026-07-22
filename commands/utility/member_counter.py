import discord
from discord.ext import commands, tasks
from discord import app_commands

from core.logger import get_logger
from database.database import get_connection

logger = get_logger("MemberCounter")


class MemberCounter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_all_counters.start()

    def cog_unload(self):
        self.update_all_counters.cancel()

    async def update_guild_counter(self, guild: discord.Guild):
        """Aktualizuje nazwę kanału z licznikiem osób dla danego serwera."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT channel_id, channel_format FROM stats_channels WHERE guild_id = ?",
            (guild.id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        channel_id, channel_format = row
        channel = guild.get_channel(channel_id)

        if not channel:
            return

        member_count = guild.member_count or len(guild.members)
        new_name = (channel_format or '👥 Osoby: {count}').format(count=member_count)

        if channel.name != new_name:
            try:
                await channel.edit(name=new_name, reason="Automatyczny odświeżacz licznika osób")
                logger.info(f"Zaktualizowano licznik osób dla serwera {guild.name}: {new_name}")
            except discord.HTTPException as e:
                logger.warning(f"Nie udało się zmienić nazwy kanału licznika na {guild.name}: {e}")
            except Exception as e:
                logger.error(f"Błąd aktualizacji licznika na {guild.name}: {e}")

    @tasks.loop(minutes=10)
    async def update_all_counters(self):
        """Cykl w tle synchronizujący liczniki wszystkich serwerów co 10 minut."""
        for guild in self.bot.guilds:
            await self.update_guild_counter(guild)

    @update_all_counters.before_loop
    async def before_update_all(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Automatyczna aktualizacja po dołączeniu nowego członka."""
        await self.update_guild_counter(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Automatyczna aktualizacja po opuszczeniu serwera przez członka."""
        await self.update_guild_counter(member.guild)

    # ==========================
    # KOMENDY SLASH
    # ==========================

    counter_group = app_commands.Group(
        name="counter",
        description="Komendy do zarządzania kanałem z licznikiem osób na serwerze"
    )

    @counter_group.command(
        name="setup",
        description="Tworzy lub konfiguruje kanał wyświetlający automatyczną ilość osób"
    )
    @app_commands.describe(
        channel="Wybierz istniejący kanał głosowy/tekstowy (lub pozostaw puste, aby stworzyć nowy)",
        text_format="Format nazwy kanału, np. '👥 Osoby: {count}' lub 'Użytkownicy: {count}'"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def counter_setup(
        self,
        interaction: discord.Interaction,
        channel: discord.VoiceChannel = None,
        text_format: str = "👥 Osoby: {count}"
    ):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        guild = interaction.guild
        member_count = guild.member_count or len(guild.members)
        formatted_name = text_format.format(count=member_count)

        try:
            if not channel:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        connect=False,
                        view_channel=True
                    )
                }
                channel = await guild.create_voice_channel(
                    name=formatted_name,
                    overwrites=overwrites,
                    reason=f"Utworzono kanał licznika osób przez {interaction.user}"
                )
            else:
                await channel.edit(name=formatted_name, reason=f"Konfiguracja licznika przez {interaction.user}")

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO stats_channels (guild_id, channel_id, channel_format)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    channel_id = excluded.channel_id,
                    channel_format = excluded.channel_format
                """,
                (guild.id, channel.id, text_format)
            )
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title="📊 Licznik Osoby Skonfigurowany",
                description=(
                    f"✅ Kanał z licznikiem osób został pomyślnie ustawiony:\n"
                    f"• **Kanał:** {channel.mention}\n"
                    f"• **Obecna nazwa:** `{formatted_name}`\n\n"
                    "Licznik będzie odświeżał się **automatycznie** przy każdym dołączeniu lub opuszczeniu serwera!"
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text="🌙 Iris Nova • Licznik Osoby")

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.exception(f"Błąd konfiguracji licznika osób: {e}")
            await interaction.followup.send(f"❌ Wystąpił błąd podczas konfiguracji: {e}", ephemeral=True)

    @counter_group.command(
        name="update",
        description="Ręcznie odświeża nazwę kanału z licznikiem osób"
    )
    async def counter_update(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        await self.update_guild_counter(interaction.guild)
        await interaction.followup.send("🔄 Wsłano polecenie odświeżenia licznika osób!", ephemeral=True)

    @counter_group.command(
        name="delete",
        description="Wyłącza automatyczny licznik osób na serwerze"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def counter_delete(self, interaction: discord.Interaction):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stats_channels WHERE guild_id = ?", (interaction.guild.id,))
        conn.commit()
        conn.close()

        await interaction.response.send_message(
            "🗑️ Usunięto powiązanie z kanałem licznika osób. Kanał nie będzie już automatycznie aktualizowany.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(MemberCounter(bot))