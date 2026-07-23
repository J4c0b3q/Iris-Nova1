import asyncio
import discord
from discord.ext import commands
from discord import app_commands

from core.logger import get_logger
from database.database import get_connection

logger = get_logger("Tickets")


class BaseTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item
    ) -> None:
        logger.error(f"Błąd w widoku ticketów ({getattr(item, 'custom_id', 'item')}): {error}")
        msg = f"❌ Wystąpił błąd: {error}"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            pass


class TicketCreateView(BaseTicketView):
    @discord.ui.button(
        label="Stwórz Ticket",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_create_btn",
        emoji="📩"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            guild = interaction.guild
            user = interaction.user

            if not guild:
                await interaction.followup.send("❌ Tej funkcji można używać tylko na serwerze.", ephemeral=True)
                return

            conn = get_connection()
            cursor = conn.cursor()

            # Pobranie ustawień ticketów dla serwera
            cursor.execute(
                """
                SELECT category_id, support_role_id, counter
                FROM ticket_settings
                WHERE guild_id = ?
                """,
                (guild.id,)
            )
            settings = cursor.fetchone()

            category_id = settings[0] if settings else None
            support_role_id = settings[1] if settings else None
            counter = (settings[2] if settings else 0) + 1

            # Sprawdzenie czy użytkownik nie ma już otwartego ticketu
            cursor.execute(
                """
                SELECT channel_id FROM tickets
                WHERE guild_id = ? AND user_id = ? AND status = 'open'
                """,
                (guild.id, user.id)
            )
            existing_tickets = cursor.fetchall()

            for (existing_ch_id,) in existing_tickets:
                ch = guild.get_channel(existing_ch_id)
                if ch:
                    conn.close()
                    await interaction.followup.send(
                        f"⚠️ Masz już otwarty ticket: {ch.mention}",
                        ephemeral=True
                    )
                    return

            # Zapisz lub zaktualizuj licznik
            if settings:
                cursor.execute(
                    "UPDATE ticket_settings SET counter = ? WHERE guild_id = ?",
                    (counter, guild.id)
                )
            else:
                cursor.execute(
                    "INSERT INTO ticket_settings (guild_id, counter) VALUES (?, ?)",
                    (guild.id, counter)
                )
            conn.commit()

            category = guild.get_channel(category_id) if category_id else None
            support_role = guild.get_role(support_role_id) if support_role_id else None

            # Account bota w gildii
            bot_member = guild.me
            if not bot_member:
                try:
                    bot_member = await guild.fetch_member(self.bot.user.id)
                except Exception:
                    bot_member = None

            # Uprawnienia dla nowego kanału
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )
            }

            if bot_member:
                overwrites[bot_member] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    manage_permissions=True
                )

            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )

            channel_name = f"ticket-{counter:04d}"
            try:
                ticket_channel = await guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    overwrites=overwrites,
                    reason=f"Ticket utworzony przez {user}"
                )
            except discord.Forbidden:
                conn.close()
                await interaction.followup.send(
                    "❌ Bot nie posiada uprawnień **Zarządzanie Kanałami (Manage Channels)** lub **Zarządzanie Uprawnieniami (Manage Permissions)**!",
                    ephemeral=True
                )
                return

            cursor.execute(
                """
                INSERT INTO tickets (guild_id, channel_id, user_id, status)
                VALUES (?, ?, ?, 'open')
                """,
                (guild.id, ticket_channel.id, user.id)
            )
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title=f"🎫 Ticket #{counter:04d}",
                description=(
                    f"Witaj {user.mention}!\n\n"
                    "Opisz swój problem lub pytanie. Zespół wsparcia odezwie się wkrótce.\n"
                    "Użyj przycisków poniżej, aby zarządzać ticketem."
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text="🌙 Iris Nova • System Ticketów")

            content = f"{user.mention}"
            if support_role:
                content += f" | {support_role.mention}"

            await ticket_channel.send(
                content=content,
                embed=embed,
                view=TicketControlView(self.bot)
            )

            await interaction.followup.send(
                f"✅ Twój ticket został utworzony: {ticket_channel.mention}",
                ephemeral=True
            )
        except Exception as e:
            logger.exception(f"Błąd podczas tworzenia ticketu: {e}")
            try:
                await interaction.followup.send(
                    f"❌ Błąd podczas tworzenia ticketu: {e}",
                    ephemeral=True
                )
            except Exception:
                pass


class TicketControlView(BaseTicketView):
    @discord.ui.button(
        label="Zamknij Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close_btn",
        emoji="🔒"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
        except Exception:
            pass

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, user_id, status FROM tickets WHERE channel_id = ?",
                (interaction.channel.id,)
            )
            ticket_data = cursor.fetchone()

            if not ticket_data:
                conn.close()
                await interaction.followup.send(
                    "❌ Ten kanał nie jest zarejestrowanym ticketem.",
                    ephemeral=True
                )
                return

            ticket_id, ticket_user_id, status = ticket_data

            cursor.execute(
                "UPDATE tickets SET status = 'closed' WHERE channel_id = ?",
                (interaction.channel.id,)
            )
            conn.commit()
            conn.close()

            ticket_author = interaction.guild.get_member(ticket_user_id)
            if ticket_author:
                try:
                    await interaction.channel.set_permissions(
                        ticket_author,
                        view_channel=True,
                        send_messages=False
                    )
                except Exception:
                    pass

            embed = discord.Embed(
                title="🔒 Ticket Zamknięty",
                description=f"Ticket został zamknięty przez {interaction.user.mention}.\nMożesz go usunąć lub otworzyć ponownie.",
                color=discord.Color.red()
            )
            embed.set_footer(text="🌙 Iris Nova")

            await interaction.followup.send(
                embed=embed,
                view=TicketClosedControlView(self.bot)
            )
        except Exception as e:
            logger.exception(f"Błąd przy zamykaniu ticketu: {e}")
            try:
                await interaction.followup.send(f"❌ Błąd przy zamykaniu ticketu: {e}", ephemeral=True)
            except Exception:
                pass

    @discord.ui.button(
        label="Dodaj osobę",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_add_user_btn",
        emoji="➕"
    )
    async def add_user_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_message(
                "💡 Aby dodać osobę do tego ticketu, użyj komendy `/ticket add @użytkownik`.",
                ephemeral=True
            )
        except Exception:
            pass


class TicketClosedControlView(BaseTicketView):
    @discord.ui.button(
        label="Usuń Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_delete_btn",
        emoji="🗑️"
    )
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_message("🗑️ Kanał ticketu zostanie usunięty za 5 sekund...")
            await asyncio.sleep(5)
            await interaction.channel.delete(reason=f"Ticket usunięty przez {interaction.user}")
        except Exception as e:
            logger.exception(f"Błąd przy usuwaniu ticketu: {e}")

    @discord.ui.button(
        label="Otwórz Ponownie",
        style=discord.ButtonStyle.success,
        custom_id="ticket_reopen_btn",
        emoji="🔓"
    )
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
        except Exception:
            pass

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id FROM tickets WHERE channel_id = ?",
                (interaction.channel.id,)
            )
            ticket_data = cursor.fetchone()

            if ticket_data:
                cursor.execute(
                    "UPDATE tickets SET status = 'open' WHERE channel_id = ?",
                    (interaction.channel.id,)
                )
                conn.commit()

                ticket_user_id = ticket_data[0]
                ticket_author = interaction.guild.get_member(ticket_user_id)
                if ticket_author:
                    try:
                        await interaction.channel.set_permissions(
                            ticket_author,
                            view_channel=True,
                            send_messages=True
                        )
                    except Exception:
                        pass

            conn.close()

            embed = discord.Embed(
                title="🔓 Ticket Ponownie Otwarty",
                description=f"Ticket został ponownie otwarty przez {interaction.user.mention}.",
                color=discord.Color.green()
            )
            embed.set_footer(text="🌙 Iris Nova")

            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.exception(f"Błąd przy ponownym otwieraniu ticketu: {e}")
            try:
                await interaction.followup.send(f"❌ Błąd: {e}", ephemeral=True)
            except Exception:
                pass


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ticket_group = app_commands.Group(
        name="ticket",
        description="Komendy zarządzania systemem ticketów"
    )

    @ticket_group.command(
        name="panel",
        description="Wysyła panel stwarzania ticketów na wybrany kanał"
    )
    @app_commands.describe(
        channel="Kanał, na którym ma pojawić się panel ticketów",
        category="Kategoria, w której będą tworzyć się kanały ticketów",
        support_role="Rola uprawniona do obsługi i zamykania ticketów"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel = None,
        category: discord.CategoryChannel = None,
        support_role: discord.Role = None
    ):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            target_channel = channel or interaction.channel

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO ticket_settings (guild_id, category_id, support_role_id)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    category_id = COALESCE(excluded.category_id, ticket_settings.category_id),
                    support_role_id = COALESCE(excluded.support_role_id, ticket_settings.support_role_id)
                """,
                (
                    interaction.guild.id,
                    category.id if category else None,
                    support_role.id if support_role else None
                )
            )
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title="🎫 Centrum Pomocy i Ticketów",
                description=(
                    "Potrzebujesz pomocy lub chcesz zadać pytanie administracji?\n\n"
                    "Kliknij przycisk **📩 Stwórz Ticket** poniżej, aby otworzyć prywatny kanał rozmowy z zespołem wsparcia."
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text="🌙 Iris Nova • System Ticketów")

            view = TicketCreateView(self.bot)

            await target_channel.send(embed=embed, view=view)
            await interaction.followup.send(
                f"✅ Panel ticketów został wysłany na kanał {target_channel.mention}!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                f"❌ Bot nie ma uprawnień do wysyłania wiadomości na kanale {target_channel.mention}!",
                ephemeral=True
            )
        except Exception as e:
            logger.exception(f"Błąd panelu: {e}")
            await interaction.followup.send(
                f"❌ Błąd podczas wysyłania panelu: {e}",
                ephemeral=True
            )

    @ticket_group.command(
        name="add",
        description="Dodaje użytkownika do obecnego ticketu"
    )
    @app_commands.describe(member="Użytkownik, którego chcesz dodać do ticketu")
    async def add(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM tickets WHERE channel_id = ?",
                (interaction.channel.id,)
            )
            ticket_data = cursor.fetchone()
            conn.close()

            if not ticket_data and not interaction.user.guild_permissions.manage_channels:
                await interaction.followup.send(
                    "❌ Ta komenda może być używana tylko na kanale ticketu.",
                    ephemeral=True
                )
                return

            await interaction.channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            )
            await interaction.followup.send(
                f"✅ Dodano {member.mention} do ticketu!",
                ephemeral=False
            )
        except Exception as e:
            logger.exception(f"Błąd dodawania użytkownika: {e}")
            await interaction.followup.send(
                f"❌ Wystąpił błąd podczas dodawania użytkownika: {e}",
                ephemeral=True
            )

    @ticket_group.command(
        name="remove",
        description="Usuwa użytkownika z obecnego ticketu"
    )
    @app_commands.describe(member="Użytkownik, którego chcesz usunąć z ticketu")
    async def remove(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM tickets WHERE channel_id = ?",
                (interaction.channel.id,)
            )
            ticket_data = cursor.fetchone()
            conn.close()

            if not ticket_data and not interaction.user.guild_permissions.manage_channels:
                await interaction.followup.send(
                    "❌ Ta komenda może być używana tylko na kanale ticketu.",
                    ephemeral=True
                )
                return

            await interaction.channel.set_permissions(member, overwrite=None)
            await interaction.followup.send(
                f"🚫 Usunięto {member.mention} z ticketu.",
                ephemeral=False
            )
        except Exception as e:
            logger.exception(f"Błąd usuwania użytkownika: {e}")
            await interaction.followup.send(
                f"❌ Wystąpił błąd podczas usuwania użytkownika: {e}",
                ephemeral=True
            )

    @ticket_group.command(
        name="close",
        description="Zamyka obecny ticket"
    )
    async def close(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
        except Exception:
            pass

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id FROM tickets WHERE channel_id = ? AND status = 'open'",
                (interaction.channel.id,)
            )
            ticket_data = cursor.fetchone()

            if not ticket_data:
                conn.close()
                await interaction.followup.send(
                    "❌ Ten kanał nie jest otwartym ticketem.",
                    ephemeral=True
                )
                return

            cursor.execute(
                "UPDATE tickets SET status = 'closed' WHERE channel_id = ?",
                (interaction.channel.id,)
            )
            conn.commit()
            conn.close()

            ticket_author = interaction.guild.get_member(ticket_data[0])
            if ticket_author:
                try:
                    await interaction.channel.set_permissions(
                        ticket_author,
                        view_channel=True,
                        send_messages=False
                    )
                except Exception:
                    pass

            embed = discord.Embed(
                title="🔒 Ticket Zamknięty",
                description=f"Ticket został zamknięty przez {interaction.user.mention}.",
                color=discord.Color.red()
            )
            embed.set_footer(text="🌙 Iris Nova")

            await interaction.followup.send(
                embed=embed,
                view=TicketClosedControlView(self.bot)
            )
        except Exception as e:
            logger.exception(f"Błąd podczas zamykania: {e}")
            await interaction.followup.send(f"❌ Błąd: {e}", ephemeral=True)

    @ticket_group.command(
        name="delete",
        description="Usuwa obecny ticket"
    )
    async def delete(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
        except Exception:
            pass

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM tickets WHERE channel_id = ?",
                (interaction.channel.id,)
            )
            ticket_data = cursor.fetchone()
            conn.close()

            if not ticket_data and not interaction.user.guild_permissions.manage_channels:
                await interaction.followup.send(
                    "❌ Ta komenda może być używana tylko na kanale ticketu.",
                    ephemeral=True
                )
                return

            await interaction.followup.send("🗑️ Kanał ticketu zostanie usunięty za 5 sekund...")
            await asyncio.sleep(5)
            await interaction.channel.delete(reason=f"Ticket usunięty przez {interaction.user}")
        except Exception as e:
            logger.exception(f"Błąd podczas usuwania: {e}")
            try:
                await interaction.followup.send(f"❌ Błąd: {e}", ephemeral=True)
            except Exception:
                pass


async def setup(bot):
    bot.add_view(TicketCreateView(bot))
    bot.add_view(TicketControlView(bot))
    bot.add_view(TicketClosedControlView(bot))
    await bot.add_cog(Tickets(bot))