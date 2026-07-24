import asyncio
import os
import discord
from discord.ext import commands
import yt_dlp

# Opcje wyszukiwania i pobierania pobierania dźwięku z YT/Audio
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extractor_args': {
        'youtube': {
            'player_client': ['ios', 'android', 'mweb'],
        }
    }
}

# Sprawdź, czy istnieje plik z ciasteczkami youtube (np. cookies.txt)
if os.path.exists('cookies.txt'):
    YTDL_OPTIONS['cookiefile'] = 'cookies.txt'
elif os.path.exists('/home/ubuntu/Iris-Nova1/cookies.txt'):
    YTDL_OPTIONS['cookiefile'] = '/home/ubuntu/Iris-Nova1/cookies.txt'

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if 'entries' in data:
            # Pobierz pierwszy wynik w przypadku wyszukiwania frazy
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # {guild_id: [YTDLSource]}

    def get_queue(self, guild_id: int):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def play_next(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        queue = self.get_queue(guild_id)

        if len(queue) > 0:
            next_track = queue.pop(0)
            voice_client = interaction.guild.voice_client

            if voice_client:
                voice_client.play(
                    next_track,
                    after=lambda e: self.play_next(interaction)
                )
                asyncio.run_coroutine_threadsafe(
                    interaction.channel.send(
                        f"🎶 **Teraz odtwarzam:** `{next_track.title}`"
                    ),
                    self.bot.loop
                )

    @discord.app_commands.command(
        name="play",
        description="Odtwarza muzykę z YouTube lub wyszukuje piosenkę"
    )
    @discord.app_commands.describe(query="Nazwa utworu lub link do YouTube")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Musisz znajdować się na kanale głosowym, aby włączyć muzykę!",
                ephemeral=True
            )
            return

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        await interaction.response.defer()

        # Połącz z kanałem głosowym, jeśli bot tam jeszcze nie przebywa
        if not voice_client:
            try:
                voice_client = await voice_channel.connect()
            except Exception as e:
                await interaction.followup.send(f"❌ Nie udało się połączyć z kanałem: {e}")
                return
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        try:
            player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Błąd podczas pobierania utworu: {e}")
            return

        queue = self.get_queue(interaction.guild.id)

        if voice_client.is_playing() or voice_client.is_paused():
            queue.append(player)
            embed = discord.Embed(
                title="🎵 Dodano do kolejki",
                description=f"[{player.title}]({player.url})",
                color=discord.Color.purple()
            )
            embed.add_field(name="Pozycja w kolejce", value=str(len(queue)))
            await interaction.followup.send(embed=embed)
        else:
            voice_client.play(
                player,
                after=lambda e: self.play_next(interaction)
            )
            embed = discord.Embed(
                title="🎶 Rozpoczęto odtwarzanie",
                description=f"[{player.title}]({player.url})",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)

    @discord.app_commands.command(
        name="skip",
        description="Pomija obecnie odtwarzany utwór"
    )
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message("⚠️ Żaden utwór nie jest obecnie odtwarzany.", ephemeral=True)
            return

        voice_client.stop()
        await interaction.response.send_message("⏭️ Pominięto obecny utwór.")

    @discord.app_commands.command(
        name="pause",
        description="Wstrzymuje odtwarzanie muzyki"
    )
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸️ Wstrzymano odtwarzanie.")
        else:
            await interaction.response.send_message("⚠️ Muzyka nie jest obecnie odtwarzana.", ephemeral=True)

    @discord.app_commands.command(
        name="resume",
        description="Wznawia wstrzymane odtwarzanie"
    )
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶️ Wznowiono odtwarzanie.")
        else:
            await interaction.response.send_message("⚠️ Odtwarzanie nie jest wstrzymane.", ephemeral=True)

    @discord.app_commands.command(
        name="stop",
        description="Zatrzymuje muzykę i czyści kolejkę"
    )
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client:
            self.queues[interaction.guild.id] = []
            voice_client.stop()
            await interaction.response.send_message("⏹️ Zatrzymano muzykę i wyczyszczono kolejkę.")
        else:
            await interaction.response.send_message("⚠️ Bot nie znajduje się na kanale głosowym.", ephemeral=True)

    @discord.app_commands.command(
        name="queue",
        description="Wyświetla aktualną kolejkę utworów"
    )
    async def queue(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue:
            await interaction.response.send_message("📜 Kolejka jest obecnie pusta.", ephemeral=True)
            return

        description = ""
        for idx, track in enumerate(queue[:10], start=1):
            description += f"**{idx}.** [{track.title}]({track.url})\n"

        if len(queue) > 10:
            description += f"\n*...oraz {len(queue) - 10} więcej utworów*"

        embed = discord.Embed(
            title="📜 Kolejka Odtwarzania Iris",
            description=description,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(
        name="leave",
        description="Rozłącza bota z kanału głosowego"
    )
    async def leave(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client:
            await voice_client.disconnect()
            self.queues[interaction.guild.id] = []
            await interaction.response.send_message("👋 Rozłączono z kanału głosowego.")
        else:
            await interaction.response.send_message("⚠️ Bot nie przebywa na żadnym kanale głosowym.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Music(bot))