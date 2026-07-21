import os
import importlib
import discord.ext.commands


async def load_extensions(bot):

    loaded = 0

    for root, dirs, files in os.walk("commands"):

        for file in files:

            if file.endswith(".py") and not file.startswith("__"):

                path = os.path.join(root, file)

                module = path.replace("\\", ".")[:-3]

                try:
                    await bot.load_extension(module)
                    print(f"✅ Załadowano: {module}")
                    loaded += 1

                except Exception as e:
                    print(
                        f"❌ Nie udało się załadować {module}: {e}"
                    )

    print(
        f"🌙 Załadowano {loaded} modułów"
    )