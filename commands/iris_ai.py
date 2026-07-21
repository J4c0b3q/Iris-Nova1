from discord.ext import commands
from ai.brain import ask_iris


class IrisAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def iris(self, ctx, *, question):
        answer = await ask_iris(question)
        await ctx.send(answer)


async def setup(bot):
    await bot.add_cog(IrisAI(bot))