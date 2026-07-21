import discord
from discord.ext import commands

from core.logger import log_info


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @discord.app_commands.command(
        name="clear",
        description="Usuwa określoną liczbę wiadomości"
    )
    @discord.app_commands.describe(
        amount="Ilość wiadomości do usunięcia"
    )
    @discord.app_commands.checks.has_permissions(
        manage_messages=True
    )
    async def clear(
        self,
        interaction: discord.Interaction,
        amount: int
    ):

        await interaction.response.defer(
            ephemeral=True
        )


        deleted = await interaction.channel.purge(
            limit=amount
        )


        await interaction.followup.send(
            f"🧹 Usunięto **{len(deleted)}** wiadomości.",
            ephemeral=True
        )


        log_info(
            f"{interaction.user} usunął {len(deleted)} wiadomości na {interaction.channel}"
        )



    @discord.app_commands.command(
        name="kick",
        description="Wyrzuca użytkownika z serwera"
    )
    @discord.app_commands.describe(
        member="Użytkownik do wyrzucenia",
        reason="Powód wyrzucenia"
    )
    @discord.app_commands.checks.has_permissions(
        kick_members=True
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Brak powodu"
    ):


        await member.kick(
            reason=reason
        )


        embed = discord.Embed(
            title="👢 Użytkownik wyrzucony",
            color=discord.Color.orange()
        )


        embed.add_field(
            name="Użytkownik",
            value=str(member)
        )

        embed.add_field(
            name="Moderator",
            value=str(interaction.user)
        )

        embed.add_field(
            name="Powód",
            value=reason,
            inline=False
        )


        await interaction.response.send_message(
            embed=embed
        )


        log_info(
            f"{interaction.user} wyrzucił {member}: {reason}"
        )



    @discord.app_commands.command(
        name="ban",
        description="Banuje użytkownika z serwera"
    )
    @discord.app_commands.describe(
        member="Użytkownik do zbanowania",
        reason="Powód bana"
    )
    @discord.app_commands.checks.has_permissions(
        ban_members=True
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Brak powodu"
    ):


        await member.ban(
            reason=reason
        )


        embed = discord.Embed(
            title="🔨 Użytkownik zbanowany",
            color=discord.Color.red()
        )


        embed.add_field(
            name="Użytkownik",
            value=str(member)
        )

        embed.add_field(
            name="Moderator",
            value=str(interaction.user)
        )

        embed.add_field(
            name="Powód",
            value=reason,
            inline=False
        )


        await interaction.response.send_message(
            embed=embed
        )


        log_info(
            f"{interaction.user} zbanował {member}: {reason}"
        )



async def setup(bot):

    await bot.add_cog(
        Moderation(bot)
    )