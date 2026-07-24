import os
import discord
from discord.ext import commands
import yt_dlp
from core.logger import get_logger

logger = get_logger("Music")

# Opcje wyszukiwania i pobierania pobierania dźwięku z YT/Audio
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
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
            'player_client': ['web_creator', 'android', 'ios', 'mweb'],
        }
    }
}

# Sprawdź, czy istnieje plik z ciasteczkami youtube (np. cookies.txt)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
possible_cookie_paths = [
    'cookies.txt',
    os.path.join(project_root, 'cookies.txt'),
    '/home/ubuntu/Iris-Nova1/cookies.txt'
]

cookies_found = False
for path in possible_cookie_paths:
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        file_size = os.path.getsize(abs_path)
        YTDL_OPTIONS['cookiefile'] = abs_path
        cookies_found = True
        logger.info(f"🍪 Załadowano plik cookies z: '{abs_path}' (Rozmiar: {file_size} bajtów)")
        break

if not cookies_found:
    logger.warning("⚠️ Nie znaleziono żadnego pliku z ciasteczkami youtube (cookies.txt). Szukano w:")
    for path in possible_cookie_paths:
        logger.warning(f"  - {os.path.abspath(path)}")

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


def get_ffmpeg_path():
    import shutil
    ffmpeg_env = os.getenv("FFMPEG_PATH", "")
    
    if ffmpeg_env:
        # Jeśli podana ścieżka jest katalogiem, spróbuj znaleźć plik wykonywalny w środku
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

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        ffmpeg_path = get_ffmpeg_path()
        return cls(discord.FFmpegPCMAudio(filename, executable=ffmpeg_path, **FFMPEG_OPTIONS), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.current_song = None

    @commands.command(name='join', help='Bot dołącza do Twojego kanału głosowego')
    async def join(self, ctx):
        if not ctx.author.voice:
            embed = discord.Embed(
                description="❌ Musisz być na kanale głosowym, abym mógł dołączyć!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False

        channel = ctx.author.voice.channel
        if ctx.voice_client:
            if ctx.voice_client.channel != channel:
                await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        return True

    @commands.command(name='leave', help='Bot opuszcza kanał głosowy')
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue.clear()
            self.current_song = None
            embed = discord.Embed(
                description="👋 Opuszczono kanał głosowy i wyczyszczono kolejkę.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Nie jestem obecnie połączony z żadnym kanałem głosowym.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    def play_next(self, ctx):
        if len(self.queue) > 0:
            self.current_song = self.queue.pop(0)
            
            # Tworzymy funkcję zwrotną po zakończeniu odtwarzania
            def after_playing(error):
                if error:
                    print(f"Błąd odtwarzacza: {error}")
                self.play_next(ctx)

            ctx.voice_client.play(self.current_song, after=after_playing)
            
            # Wysłanie wiadomości o nowo granym utworze (asynchronicznie)
            self.bot.loop.create_task(
                ctx.send(embed=discord.Embed(
                    description=f"🎵 Teraz gram: **{self.current_song.title}**",
                    color=discord.Color.green()
                ))
            )
        else:
            self.current_song = None

    @commands.command(name='play', help='Odtwarza utwór z YouTube (link lub wyszukiwanie tekstowe)')
    async def play(self, ctx, *, search: str):
        # Dołącz do kanału jeśli jeszcze cię tam nie ma
        joined = await self.join(ctx)
        if not joined:
            return

        async with ctx.typing():
            try:
                # Pobierz utwór jako strumień
                player = await YTDLSource.from_url(search, loop=self.bot.loop, stream=True)
            except Exception as e:
                embed = discord.Embed(
                    title="⚠️ Błąd",
                    description=f"Wystąpił błąd podczas pobierania utworu: {e}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                self.queue.append(player)
                embed = discord.Embed(
                    description=f"📝 Dodano do kolejki: **{player.title}**",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                self.current_song = player
                
                def after_playing(error):
                    if error:
                        print(f"Błąd odtwarzacza: {error}")
                    self.play_next(ctx)

                ctx.voice_client.play(player, after=after_playing)
                embed = discord.Embed(
                    description=f"🎵 Teraz gram: **{player.title}**",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)

    @commands.command(name='pause', help='Wstrzymuje odtwarzanie utworu')
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = discord.Embed(
                description="⏸️ Odtwarzanie wstrzymane.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Nic aktualnie nie jest odtwarzane.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='resume', help='Wznawia odtwarzanie utworu')
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = discord.Embed(
                description="▶️ Wznowiono odtwarzanie.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Odtwarzanie nie jest wstrzymane.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='skip', help='Pomija aktualnie odtwarzany utwór')
    async def skip(self, ctx):
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            embed = discord.Embed(
                description="⏭️ Pominięto utwór.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Nic obecnie nie jest odtwarzane.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='queue', aliases=['q'], help='Pokazuje aktualną kolejkę utworów')
    async def queue_info(self, ctx):
        if not self.current_song and len(self.queue) == 0:
            embed = discord.Embed(
                description="📭 Kolejka jest obecnie pusta.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🎶 Kolejka utworów",
            color=discord.Color.blue()
        )
        
        if self.current_song:
            embed.add_field(name="Now playing", value=f"🎵 **{self.current_song.title}**", inline=False)
        
        if len(self.queue) > 0:
            queue_list = ""
            for i, song in enumerate(self.queue, start=1):
                queue_list += f"{i}. **{song.title}**\n"
            embed.add_field(name="Następne w kolejce", value=queue_list, inline=False)
        else:
            embed.add_field(name="Następne w kolejce", value="Brak utworów w kolejce.", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='stop', help='Zatrzymuje odtwarzanie i czyści kolejkę')
    async def stop(self, ctx):
        if ctx.voice_client:
            self.queue.clear()
            self.current_song = None
            ctx.voice_client.stop()
            embed = discord.Embed(
                description="⏹️ Zatrzymano odtwarzacz i wyczyszczono kolejkę.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Nie jestem obecnie połączony z żadnym kanałem głosowym.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))