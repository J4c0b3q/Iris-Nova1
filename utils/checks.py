from discord.ext import commands

from core.env import Env


def is_owner():

    async def predicate(ctx):
        return ctx.author.id == Env.OWNER_ID

    return commands.check(predicate)