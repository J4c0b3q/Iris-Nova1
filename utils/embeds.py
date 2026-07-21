import discord


def success(message: str):
    return discord.Embed(
        description=f"✅ {message}",
        color=0x57F287,
    )


def error(message: str):
    return discord.Embed(
        description=f"❌ {message}",
        color=0xED4245,
    )


def warning(message: str):
    return discord.Embed(
        description=f"⚠️ {message}",
        color=0xFEE75C,
    )


def info(message: str):
    return discord.Embed(
        description=f"ℹ️ {message}",
        color=0x5865F2,
    )