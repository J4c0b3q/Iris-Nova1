import discord
from discord.ext import commands

from core.base_cog import BaseCog
from core.constants import EMBED_COLOR


def parse_color(color_input: str) -> discord.Color:
    if not color_input:
        return EMBED_COLOR
    color_input = color_input.strip().lower()
    color_map = {
        "czerwony": discord.Color.red(),
        "red": discord.Color.red(),
        "zielony": discord.Color.green(),
        "green": discord.Color.green(),
        "niebieski": discord.Color.blue(),
        "blue": discord.Color.blue(),
        "złoty": discord.Color.gold(),
        "zloty": discord.Color.gold(),
        "gold": discord.Color.gold(),
        "fioletowy": discord.Color.purple(),
        "purple": discord.Color.purple(),
        "pomarańczowy": discord.Color.orange(),
        "pomaranczowy": discord.Color.orange(),
        "orange": discord.Color.orange(),
        "czarny": discord.Color.dark_theme(),
        "black": discord.Color.default(),
    }
    if color_input in color_map:
        return color_map[color_input]
    if color_input.startswith("#"):
        color_input = color_input[1:]
    try:
        return discord.Color(int(color_input, 16))
    except ValueError:
        return EMBED_COLOR


class Basic(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.hybrid_command(
        name="ping",
        description="Pokazuje aktualne opóźnienie bota."
    )
    async def ping(self, ctx: commands.Context):

        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Opóźnienie: **{latency} ms**",
            color=EMBED_COLOR,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="say",
        aliases=["ogloszenie", "embed", "sendmsg"],
        description="Wysyła wiadomość/ogłoszenie/regulamin na wskazany kanał jako bot."
    )
    @discord.app_commands.describe(
        tresc="Treść wiadomości do wysłania (użyj \\n aby zrobić nową linię)",
        tytul="Tytuł wiadomości (tworzy nagłówek Embed)",
        kanal="Kanał, na który ma zostać wysłana wiadomość (opcjonalnie)",
        kolor="Kolor ramki Embed (np. #ff0000, red, green, gold, blue, purple)",
        obraz="Link URL do obrazka/grafiki dołączanej do ogłoszenia",
        ping="Oznaczenie grupy/osoby (np. @everyone, @here)",
        zwykla_wiadomosc="Ustaw na True, aby wysłać czysty tekst bez ramki Embed"
    )
    @commands.has_permissions(manage_messages=True)
    async def say(
        self,
        ctx: commands.Context,
        tresc: str,
        tytul: str = None,
        kanal: discord.TextChannel = None,
        kolor: str = None,
        obraz: str = None,
        ping: str = None,
        zwykla_wiadomosc: bool = False,
    ):
        if not ctx.guild:
            await ctx.send("❌ Ta komenda może być używana tylko na serwerze.", ephemeral=True)
            return

        target_channel = kanal or ctx.channel

        # Formatowanie nowej linii
        formatted_content = tresc.replace("\\n", "\n")

        ping_text = f"{ping} " if ping else ""

        if zwykla_wiadomosc:
            full_msg = f"{ping_text}{formatted_content}"
            if tytul:
                full_msg = f"{ping_text}**{tytul}**\n\n{formatted_content}"

            await target_channel.send(content=full_msg)
        else:
            embed_color = parse_color(kolor)
            embed = discord.Embed(
                title=tytul,
                description=formatted_content,
                color=embed_color,
            )

            if obraz:
                embed.set_image(url=obraz)

            embed.set_footer(
                text=f"🌙 {ctx.guild.name}",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None
            )

            await target_channel.send(content=ping if ping else None, embed=embed)

        if ctx.interaction:
            await ctx.send(
                f"✅ Wiadomość została pomyślnie wysłana na kanał {target_channel.mention}!",
                ephemeral=True
            )
        else:
            try:
                await ctx.message.delete()
            except Exception:
                pass


async def setup(bot):
    await bot.add_cog(Basic(bot))