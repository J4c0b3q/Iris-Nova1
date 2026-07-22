from discord.ext import commands

from core.env import Env


def is_owner():

    async def predicate(ctx):
        if Env.OWNER_ID and ctx.author.id == Env.OWNER_ID:
            return True
        return await ctx.bot.is_owner(ctx.author)

    return commands.check(predicate)