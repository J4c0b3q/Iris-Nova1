import asyncio
import discord
from discord.ext import commands
import yt_dlp

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
}

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

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, guild_id: int):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def play_next(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if len(queue) > 0:
            next_track = queue.pop(0)
            voice_client = interaction.guild.voice_client
            if voice_client:
                voice_client.play(next_track, after=lambda e: self.play_next(interaction))
                asyncio.run_coroutine_threadsafe(
                    interaction.channel.send(f"🎶 **Teraz odtwarzam:** `{next_track.title}`"),
                    self.bot.loop
                )

    @discord.app_commands.command(name="play", description="Odtwarza muzykę z YT lub wyszukuje piosenkę")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Musisz być na kanale głosowym!", ephemeral=True)
            return

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        await interaction.response.defer()

        if not voice_client:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
        queue = self.get_queue(interaction.guild.id)

        if voice_client.is_playing() or voice_client.is_paused():
            queue.append(player)
            await interaction.followup.send(f"🎵 Dodano do kolejki: **{player.title}**")
        else:
            voice_client.play(player, after=lambda e: self.play_next(interaction))
            await interaction.followup.send(f"🎶 Odtwarzam: **{player.title}**")

    @discord.app_commands.command(name="skip", description="Pomija obecny utwór")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("⏭️ Pominięto utwór.")
        else:
            await interaction.response.send_message("⚠️ Nic nie gra.", ephemeral=True)

    @discord.app_commands.command(name="stop", description="Zatrzymuje odtwarzanie i czyści kolejkę")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client:
            self.queues[interaction.guild.id] = []
            voice_client.stop()
            await interaction.response.send_message("⏹️ Zatrzymano muzykę.")

async def setup(bot):
    await bot.add_cog(Music(bot))