import asyncio
import os
import discord
from discord.ext import commands
import yt_dlp
from core.logger import get_logger

logger = get_logger("Music")

# Opcje wyszukiwania i pobierania dźwięku z innych platform (np. SoundCloud, Bandcamp)
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
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
    }
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


def get_ffmpeg_path():
    import shutil
    ffmpeg_env = os.getenv("FFMPEG_PATH", "")
    
    if ffmpeg_env:
        if os.path.isdir(ffmpeg_env):
            for name in ["ffmpeg.exe", "ffmpeg"]:
                full_path = os.path.join(ffmpeg_env, name)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    logger.info(f"⚙️ FFMPEG_PATH wskazuje na katalog. Automatycznie wybrano plik: {full_path}")
                    return full_path
            logger.warning(f"⚠️ FFMPEG_PATH wskazuje na katalog '{ffmpeg_env}', ale nie znaleziono w nim pliku 'ffmpeg.exe' ani 'ffmpeg'.")
        else:
            if os.path.exists(ffmpeg_env) and os.path.isfile(ffmpeg_env):
                return ffmpeg_env
            logger.warning(f"⚠️ Plik FFMPEG_PATH '{ffmpeg_env}' nie istnieje lub nie jest poprawnym plikiem.")

    # Próba znalezienia w zmiennych środowiskowych systemowych (PATH)
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # Domyślny fallback
    return "ffmpeg"


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
        
        # Słownik opcji z możliwością użycia cookies (jeśli plik istnieje)
        opts = YTDL_OPTIONS.copy()
        if os.path.exists("cookies.txt"):
            opts['cookiefile'] = "cookies.txt"
            logger.info("🍪 Wykryto plik cookies.txt. Używam do uwierzytelniania w yt-dlp.")
            
        custom_ytdl = yt_dlp.YoutubeDL(opts)
        
        data = await loop.run_in_executor(
            None, lambda: custom_ytdl.extract_info(url, download=not stream)
        )

        if 'entries' in data:
            # Pobierz pierwszy wynik w przypadku wyszukiwania frazy
            data = data['entries'][0]

        filename = data['url'] if stream else custom_ytdl.prepare_filename(data)
        ffmpeg_path = get_ffmpeg_path()

        # Pobieramy zalecane nagłówki HTTP wygenerowane przez yt_dlp dla tego utworu
        http_headers = data.get('http_headers') or {}
        
        # Upewniamy się, że mamy prawidłowy User-Agent
        if 'User-Agent' not in http_headers:
            http_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

        # Tworzymy ciąg nagłówków rozdzielonych CRLF (\r\n) wymagany przez FFmpeg
        headers_str = "".join(f"{k}: {v}\r\n" for k, v in http_headers.items())

        # Klonujemy bazowe ustawienia i dodajemy dynamiczne nagłówki do before_options
        instance_ffmpeg_options = FFMPEG_OPTIONS.copy()
        instance_ffmpeg_options['before_options'] = (
            f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
            f'-headers "{headers_str}"'
        )

        return cls(discord.FFmpegPCMAudio(filename, executable=ffmpeg_path, **instance_ffmpeg_options), data=data)


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
        description="Odtwarza muzykę ze SoundCloud, Bandcamp, Twitch lub innych alternatywnych serwisów"
    )
    @discord.app_commands.describe(
        query="Nazwa utworu, bezpośredni link (SoundCloud, Bandcamp itp.) lub link do streamu",
        source="Serwis do wyszukiwania utworu, jeśli nie podano pełnego linku"
    )
    @discord.app_commands.choices(source=[
        discord.app_commands.Choice(name="SoundCloud ☁️", value="scsearch"),
        discord.app_commands.Choice(name="Bandcamp 🎸", value="bcsearch")
    ])
    async def play(self, interaction: discord.Interaction, query: str, source: discord.app_commands.Choice[str] = None):
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

        # Jeśli to nie jest bezpośredni URL, zastosuj odpowiedni prefiks wyszukiwania (domyślnie SoundCloud)
        is_url = query.startswith("http://") or query.startswith("https://")
        if not is_url:
            search_prefix = source.value if source else "scsearch"
            # Zabezpieczenie, aby nie dodawać podwójnie prefiksów
            if not any(query.startswith(prefix) for prefix in ["scsearch:", "bcsearch:", "soundgasm:"]):
                query = f"{search_prefix}:{query}"
        else:
            # Sprawdzenie i zablokowanie linków do YouTube, jeśli użytkownik mimo wszystko wklei taki link
            if "youtube.com" in query.lower() or "youtu.be" in query.lower():
                await interaction.followup.send(
                    "❌ Odtwarzanie z serwisu YouTube zostało wyłączone na tym botie. "
                    "Wklej link z SoundCloud, Bandcamp lub wyszukaj wpisując samą nazwę piosenki."
                )
                return

        # Wykrywanie i obsługa zabezpieczeń DRM z fallbackiem do wyszukiwania SoundCloud lub YouTube (jeśli dozwolone)
        try:
            player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
        except Exception as e:
            error_str = str(e)
            if "DRM protected" in error_str or "2195763135" in query:
                await interaction.followup.send("⚠️ Ten utwór jest zabezpieczony przez DRM (SoundCloud Go+). Próbuję wyszukać darmową alternatywę...", ephemeral=False)
                try:
                    # Wyciągamy samą nazwę utworu z linku lub upraszczamy zapytanie
                    search_query = query
                    if is_url:
                        # Próba uproszczenia nazwy z adresu URL
                        parts = query.split('/')
                        if len(parts) > 3:
                            # np. artist-name-track-name
                            raw_name = parts[-1].replace('-', ' ')
                            search_query = f"scsearch:{raw_name}"
                        else:
                            search_query = "scsearch:music"
                    else:
                        # Jeśli to była nazwa ze scsearch, usuwamy prefiks i szukamy ponownie
                        search_query = query.replace("scsearch:", "")
                        search_query = f"scsearch:{search_query} free"
                    
                    logger.info(f"DRM Fallback: Szukam alternatywy dla: {search_query}")
                    player = await YTDLSource.from_url(search_query, loop=self.bot.loop, stream=True)
                except Exception as fallback_err:
                    await interaction.followup.send(f"❌ Nie udało się automatycznie obejść blokady DRM: {fallback_err}")
                    return
            else:
                await interaction.followup.send(f"❌ Błąd podczas pobierania lub odtwarzania utworu: {e}")
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
