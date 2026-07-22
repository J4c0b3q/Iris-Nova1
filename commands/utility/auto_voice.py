import discord
from discord.ext import commands
from discord import app_commands

from core.logger import get_logger
from database.database import get_connection

logger = get_logger("AutoVoice")


class AutoVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    voice_group = app_commands.Group(
        name="voice",
        description="Komendy do zarządzania automatycznymi kanałami głosowymi"
    )

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        """Obsługa tworzenia i usuwania tymczasowych kanałów głosowych."""
        if member.bot:
            return

        conn = get_connection()
        cursor = conn.cursor()

        # 1. DOŁĄCZENIE DO KANAŁU TWORZĄCEGO (TRIGGER)
        if after.channel is not None and (before.channel != after.channel):
            guild = member.guild

            # Pobranie skonfigurowanego kanału triggera z bazy
            cursor.execute(
                "SELECT channel_id, category_id FROM autovoice_settings WHERE guild_id = ?",
                (guild.id,)
            )
            setting = cursor.fetchone()

            is_trigger = False
            target_category = after.channel.category

            if setting and setting[0] == after.channel.id:
                is_trigger = True
                if setting[1]:
                    cat = guild.get_channel(setting[1])
                    if cat and isinstance(cat, discord.CategoryChannel):
                        target_category = cat
            else:
                # Domyślne rozpoznawanie po nazwie kanału
                ch_name = after.channel.name.lower().strip()
                if ch_name in ["autokanał", "autokanal", "➕ stwórz kanał", "stwórz kanał", "stworz kanal", "autochannel", "stworz-kanal"]:
                    is_trigger = True

            if is_trigger:
                channel_name = f"🔊 {member.display_name}"
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        view_channel=True,
                        connect=True,
                        speak=True
                    ),
                    member: discord.PermissionOverwrite(
                        view_channel=True,
                        connect=True,
                        speak=True,
                        manage_channels=True,
                        move_members=True,
                        mute_members=True,
                        deafen_members=True
                    )
                }

                # Klonowanie uprawnień z kategorii/kanału triggera jeśli istnieją
                if target_category:
                    for target, overwrite in target_category.overwrites.items():
                        if target not in overwrites:
                            overwrites[target] = overwrite

                try:
                    new_channel = await guild.create_voice_channel(
                        name=channel_name,
                        category=target_category,
                        overwrites=overwrites,
                        reason=f"Autokanał utworzony dla {member.display_name}"
                    )

                    # Przenosimy użytkownika do nowego kanału
                    await member.move_to(new_channel)

                    # Zapisujemy do bazy danych
                    cursor.execute(
                        "INSERT INTO temp_voice_channels (channel_id, guild_id, owner_id) VALUES (?, ?, ?)",
                        (new_channel.id, guild.id, member.id)
                    )
                    conn.commit()

                    # Wysyłamy panel zarządzania / komendy na czat kanału
                    try:
                        embed = discord.Embed(
                            title=f"🎙️ Zarządzanie Kanałem • {member.display_name}",
                            description=(
                                f"Witaj {member.mention}! Twój prywatny kanał głosowy został pomyślnie utworzony.\n\n"
                                "Jako właściciel kanału możesz nim zarządzać używając poniższych komend:"
                            ),
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="✏️ `/voice name <nazwa>`", value="Zmienia nazwę Twojego kanału", inline=False)
                        embed.add_field(name="👥 `/voice limit <liczba>`", value="Ustawia limit osób (0 = brak limitu)", inline=False)
                        embed.add_field(name="🔒 `/voice lock`", value="Blokuje kanał przed innymi", inline=False)
                        embed.add_field(name="🔓 `/voice unlock`", value="Odblokowuje kanał dla wszystkich", inline=False)
                        embed.add_field(name="✅ `/voice permit <użytkownik>`", value="Zezwala konkretnej osobie na dołączenie", inline=False)
                        embed.add_field(name="👢 `/voice kick <użytkownik>`", value="Wyrzuca osobę z Twojego kanału", inline=False)
                        embed.set_footer(text="🌙 Iris Nova • Autokanały Głosowe")

                        await new_channel.send(content=member.mention, embed=embed)
                    except Exception as msg_err:
                        logger.warning(f"Nie udało się wysłać wiadomości powitalnej na kanał {new_channel.id}: {msg_err}")

                    logger.info(f"Utworzono autokanał {new_channel.name} ({new_channel.id}) dla {member}")
                except Exception as e:
                    logger.error(f"Błąd tworzenia autokanału głosowego: {e}")

        # 2. OPUŚCZENIE KANAŁU - USUNIĘCIE JEŚLI PUSTY
        if before.channel is not None and (before.channel != after.channel):
            ch_id = before.channel.id
            cursor.execute(
                "SELECT owner_id FROM temp_voice_channels WHERE channel_id = ?",
                (ch_id,)
            )
            row = cursor.fetchone()

            if row:
                if len(before.channel.members) == 0:
                    try:
                        await before.channel.delete(reason="Wszyscy opuścili tymczasowy kanał głosowy.")
                        cursor.execute("DELETE FROM temp_voice_channels WHERE channel_id = ?", (ch_id,))
                        conn.commit()
                        logger.info(f"Usunięto pusty autokanał ID {ch_id}")
                    except Exception as e:
                        logger.error(f"Nie udało się usunąć tymczasowego kanału {ch_id}: {e}")

        conn.close()

    # ==========================
    # KOMENDY ZARZĄDZANIA KANAŁEM
    # ==========================

    def _get_user_temp_channel(self, interaction: discord.Interaction):
        """Pomocnicza funkcja pobierająca kanał, w którym znajduje się użytkownik oraz weryfikująca właściciela."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            return None, "❌ Musisz znajdować się na swoim tymczasowym kanale głosowym!"

        channel = interaction.user.voice.channel
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT owner_id FROM temp_voice_channels WHERE channel_id = ?",
            (channel.id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None, "❌ Ten kanał głosowy nie jest zarządzanym autokanałem!"

        owner_id = row[0]
        if owner_id != interaction.user.id and not interaction.user.guild_permissions.manage_channels:
            return None, "❌ Tylko właściciel tego autokanału może nim zarządzać!"

        return channel, None

    @voice_group.command(
        name="setup",
        description="Konfiguruje główny kanał tworzący (autokanał) dla serwera"
    )
    @app_commands.describe(
        channel="Kanał głosowy, po wejściu na który tworzy się nowy kanał",
        category="Kategoria, w której mają tworzyć się nowe kanały"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        channel: discord.VoiceChannel = None,
        category: discord.CategoryChannel = None
    ):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        guild = interaction.guild

        try:
            if not channel:
                target_cat = category or interaction.channel.category
                channel = await guild.create_voice_channel(
                    name="➕ Stwórz kanał",
                    category=target_cat,
                    reason=f"Konfiguracja autokanału przez {interaction.user}"
                )

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO autovoice_settings (guild_id, channel_id, category_id)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    channel_id = excluded.channel_id,
                    category_id = excluded.category_id
                """,
                (guild.id, channel.id, category.id if category else (channel.category.id if channel.category else None))
            )
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title="🔊 Konfiguracja Autokanałów",
                description=(
                    f"✅ Pomyślnie ustawiono kanał tworzący: {channel.mention}\n"
                    "Wejście na ten kanał automatycznie utworzy prywatny kanał głosowy dla użytkownika!"
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text="🌙 Iris Nova • Autokanały")

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.exception(f"Błąd podczas konfiguracji autokanału: {e}")
            await interaction.followup.send(f"❌ Błąd podczas konfiguracji: {e}", ephemeral=True)

    @voice_group.command(
        name="name",
        description="Zmienia nazwę Twojego tymczasowego kanału głosowego"
    )
    @app_commands.describe(new_name="Nowa nazwa dla kanału")
    async def name(self, interaction: discord.Interaction, new_name: str):
        channel, err = self._get_user_temp_channel(interaction)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return

        try:
            await channel.edit(name=new_name)
            await interaction.response.send_message(
                f"✅ Zmieniono nazwę kanału na: **{new_name}**",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Wystąpił błąd podczas zmiany nazwy: {e}",
                ephemeral=True
            )

    @voice_group.command(
        name="limit",
        description="Ustawia limit użytkowników na Twoim kanale (0 = brak limitu)"
    )
    @app_commands.describe(user_limit="Liczba miejsc (0-99)")
    async def limit(self, interaction: discord.Interaction, user_limit: int):
        channel, err = self._get_user_temp_channel(interaction)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return

        user_limit = max(0, min(99, user_limit))

        try:
            await channel.edit(user_limit=user_limit)
            limit_text = "brak limitu" if user_limit == 0 else f"{user_limit} osób"
            await interaction.response.send_message(
                f"✅ Ustawiono limit kanału na: **{limit_text}**",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Wystąpił błąd podczas ustawiania limitu: {e}",
                ephemeral=True
            )

    @voice_group.command(
        name="lock",
        description="Zablokowuje Twój kanał (uniemożliwia dołączanie innym)"
    )
    async def lock(self, interaction: discord.Interaction):
        channel, err = self._get_user_temp_channel(interaction)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return

        try:
            await channel.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.response.send_message(
                "🔒 Kanał został zablokowany dla reszty serwera.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Błąd: {e}", ephemeral=True)

    @voice_group.command(
        name="unlock",
        description="Odblokowuje Twój kanał głosowy"
    )
    async def unlock(self, interaction: discord.Interaction):
        channel, err = self._get_user_temp_channel(interaction)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return

        try:
            await channel.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.response.send_message(
                "🔓 Kanał został odblokowany.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Błąd: {e}", ephemeral=True)

    @voice_group.command(
        name="permit",
        description="Zezwala konkretnemu użytkownikowi na dołączenie do zablokowanego kanału"
    )
    @app_commands.describe(member="Użytkownik, któremu chcesz dać dostęp")
    async def permit(self, interaction: discord.Interaction, member: discord.Member):
        channel, err = self._get_user_temp_channel(interaction)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return

        try:
            await channel.set_permissions(member, connect=True, view_channel=True)
            await interaction.response.send_message(
                f"✅ Dopuszczono {member.mention} do kanału!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Błąd: {e}", ephemeral=True)

    @voice_group.command(
        name="kick",
        description="Wyrzuca wskazanego użytkownika z Twojego kanału głosowego"
    )
    @app_commands.describe(member="Użytkownik do wyrzucenia z kanału")
    async def kick(self, interaction: discord.Interaction, member: discord.Member):
        channel, err = self._get_user_temp_channel(interaction)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return

        if member.voice and member.voice.channel == channel:
            try:
                await member.move_to(None)
                await channel.set_permissions(member, connect=False)
                await interaction.response.send_message(
                    f"🚫 Wyrzucono {member.mention} z kanału i zablokowano mu ponowne wejście.",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(f"❌ Błąd: {e}", ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Ten użytkownik nie znajduje się obecnie na Twoim kanale!",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(AutoVoice(bot))