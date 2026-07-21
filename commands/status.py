from discord.ext import commands
from discord import Activity, ActivityType
from core.config import BOT_NAME, VERSION, SETTINGS
import time


start_time = time.time()


class Status(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(
            activity=Activity(
                type=ActivityType.playing,
                name=f"!help | {BOT_NAME}"
            )
        )


    @commands.command()
    async def irisinfo(self, ctx):

        uptime = int(time.time() - start_time)

        hours = uptime // 3600
        minutes = (uptime % 3600) // 60

        members = sum(
            g.member_count or 0
            for g in self.bot.guilds
        )

        ai_status = (
            "🟢 ON"
            if SETTINGS["AI_ENABLED"]
            else "🔴 OFF"
        )

        await ctx.send(
            f"""
🌙 **{BOT_NAME}**

🟢 Status: Online

⏱️ Czas działania:
{hours}h {minutes}m

🌐 Serwery:
{len(self.bot.guilds)}

👥 Użytkownicy:
{members}

🧠 AI:
{ai_status}

⚙️ Wersja:
{VERSION}
"""
        )


async def setup(bot):
    await bot.add_cog(Status(bot))