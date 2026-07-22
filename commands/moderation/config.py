import discord
from discord.ext import commands
from database.database import get_connection

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="setup",
        description="Konfiguracja kanałów logów oraz powitań dla serwera Iris"
    )
    @discord.app_commands.describe(
        option="Co chcesz skonfigurować",
        channel="Wybierz kanał tekstowy (opcjonalnie, domyślnie obecny kanał)"
    )
    @discord.app_commands.choices(
        option=[
            discord.app_commands.Choice(
                name="👥 Logi członków (dołączenia / opuszczenia)",
                value="member_logs"
            ),
            discord.app_commands.Choice(
                name="🛡️ Logi moderacji (bany / wyciszenia / kary)",
                value="moderation_logs"
            ),
            discord.app_commands.Choice(
                name="💬 Logi wiadomości (usunięcia / komendy)",
                value="message_logs"
            ),
            discord.app_commands.Choice(
                name="📝 Główny kanał logów (wszystkie 3 typy logów)",
                value="logs"
            ),
            discord.app_commands.Choice(
                name="👋 Kanał powitań",
                value="welcome"
            )
        ]
    )
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        option: str,
        channel: discord.TextChannel = None
    ):
        target_channel = channel or interaction.channel
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT OR IGNORE INTO guilds (guild_id) VALUES (?)", (interaction.guild.id,))

        if option == "member_logs":
            cursor.execute("UPDATE guilds SET member_log_channel = ? WHERE guild_id = ?", (target_channel.id, interaction.guild.id))
            message = f"✅ Kanał logów członków ustawiony na: {target_channel.mention}"
        elif option == "moderation_logs":
            cursor.execute("UPDATE guilds SET moderation_log_channel = ? WHERE guild_id = ?", (target_channel.id, interaction.guild.id))
            message = f"✅ Kanał logów moderacji ustawiony na: {target_channel.mention}"
        elif option == "message_logs":
            cursor.execute("UPDATE guilds SET message_log_channel = ? WHERE guild_id = ?", (target_channel.id, interaction.guild.id))
            message = f"✅ Kanał logów wiadomości ustawiony na: {target_channel.mention}"
        elif option == "logs":
            cursor.execute(
                "UPDATE guilds SET log_channel = ?, member_log_channel = ?, moderation_log_channel = ?, message_log_channel = ? WHERE guild_id = ?",
                (target_channel.id, target_channel.id, target_channel.id, target_channel.id, interaction.guild.id)
            )
            message = f"✅ Główny kanał logów (wszystkie rodzaje) ustawiony na: {target_channel.mention}"
        elif option == "welcome":
            cursor.execute("UPDATE guilds SET welcome_channel = ? WHERE guild_id = ?", (target_channel.id, interaction.guild.id))
            message = f"✅ Kanał powitań ustawiony na: {target_channel.mention}"

        conn.commit()
        conn.close()
        await interaction.response.send_message(message, ephemeral=True)

    @discord.app_commands.command(
        name="config",
        description="Pokazuje pełną konfigurację kanałów Iris"
    )
    async def config(self, interaction: discord.Interaction):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT log_channel, member_log_channel, moderation_log_channel, message_log_channel, welcome_channel, prefix FROM guilds WHERE guild_id = ?",
            (interaction.guild.id,)
        )
        data = cursor.fetchone()
        conn.close()

        if not data:
            await interaction.response.send_message("⚠️ Ten serwer nie ma jeszcze skonfigurowanych kanałów. Użyj `/setup`.", ephemeral=True)
            return

        def get_ch_mention(ch_id):
            if not ch_id:
                return "Nie ustawiono"
            ch = interaction.guild.get_channel(ch_id)
            return ch.mention if ch else "Nie odnaleziono kanału"

        embed = discord.Embed(title="⚙️ Pełna Konfiguracja Iris Nova", color=discord.Color.blue())
        embed.add_field(name="👥 Logi Członków", value=get_ch_mention(data[1]), inline=True)
        embed.add_field(name="🛡️ Logi Moderacji", value=get_ch_mention(data[2]), inline=True)
        embed.add_field(name="💬 Logi Wiadomości", value=get_ch_mention(data[3]), inline=True)
        embed.add_field(name="📝 Główny Log", value=get_ch_mention(data[0]), inline=True)
        embed.add_field(name="👋 Kanał Powitań", value=get_ch_mention(data[4]), inline=True)
        embed.add_field(name="🔧 Prefix", value=f"`{data[5] or '!'}`", inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Config(bot))