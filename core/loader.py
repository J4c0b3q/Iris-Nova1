import os


async def load_extensions(bot):

    loaded = 0
    failed = 0

    folders = [
        "commands",
        "events"
    ]

    for folder in folders:

        if not os.path.exists(folder):
            continue

        for root, dirs, files in os.walk(folder):

            for file in files:

                if (
                    file.endswith(".py")
                    and not file.startswith("__")
                ):

                    path = os.path.join(root, file)

                    module = (
                        path
                        .replace("\\", ".")
                        .replace("/", ".")[:-3]
                    )

                    try:
                        await bot.load_extension(module)

                        print(
                            f"✅ Załadowano: {module}"
                        )

                        loaded += 1


                    except Exception as e:

                        print(
                            f"❌ Błąd {module}: {e}"
                        )

                        failed += 1


    print(
        f"🌙 Moduły: {loaded} załadowane | {failed} błędów"
    )