import discord
from discord.ext import commands

from core.config import OWNER_ID
from core.logger import log_info


class Owner(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    def is_owner(self, interaction):

        return interaction.user.id == OWNER_ID



    @discord.app_commands.command(
        name="reload",
        description="Przeładowuje moduły Iris"
    )
    @discord.app_commands.describe(
        extension="Nazwa modułu bez commands."
    )
    async def reload(
        self,
        interaction: discord.Interaction,
        extension: str = None
    ):


        if not self.is_owner(interaction):

            await interaction.response.send_message(
                "❌ Brak dostępu.",
                ephemeral=True
            )

            return



        extensions = [

            "commands.basic",
            "commands.iris_ai",
            "commands.welcome",
            "commands.moderation",
            "commands.errors",
            "commands.owner",
            "commands.status",
            "commands.help",
            "commands.config",
            "commands.modconfig",
            "commands.warnings"

        ]



        if extension:

            try:

                await self.bot.reload_extension(
                    f"commands.{extension}"
                )


                await interaction.response.send_message(
                    f"♻️ Przeładowano moduł: `{extension}`"
                )


            except Exception as e:


                await interaction.response.send_message(
                    f"❌ Błąd reload:\n```{e}```"
                )


            return



        await interaction.response.defer(
            ephemeral=True
        )


        for ext in extensions:

            try:

                await self.bot.reload_extension(
                    ext
                )


            except Exception as e:

                await interaction.followup.send(
                    f"❌ Błąd przy `{ext}`:\n```{e}```"
                )

                return



        await interaction.followup.send(
            "♻️ Przeładowano wszystkie moduły Iris."
        )


        log_info(
            f"{interaction.user} przeładował wszystkie moduły"
        )



async def setup(bot):

    await bot.add_cog(
        Owner(bot)
    )