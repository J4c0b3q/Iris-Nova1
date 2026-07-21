import discord
from discord.ext import commands
import datetime
import time

from database.database import get_connection


class AutoMod(commands.Cog):

    def __init__(self, bot):

        self.bot = bot
        self.message_cache = {}



    async def get_settings(
        self,
        guild_id
    ):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT anti_spam, anti_links, anti_caps
            FROM automod_settings
            WHERE guild_id = ?
            """,
            (guild_id,)
        )


        data = cursor.fetchone()

        conn.close()


        return data if data else (1,1,1)



    async def add_warn(
        self,
        guild,
        user,
        reason
    ):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT INTO warnings
            (
                guild_id,
                user_id,
                moderator_id,
                reason
            )
            VALUES (?,?,?,?)
            """,
            (
                guild.id,
                user.id,
                self.bot.user.id,
                reason
            )
        )


        conn.commit()
        conn.close()



    async def timeout_user(
        self,
        member
    ):

        try:

            until = (
                datetime.datetime.now(
                    datetime.timezone.utc
                )
                +
                datetime.timedelta(
                    minutes=2
                )
            )


            await member.timeout(
                until,
                reason="Iris AutoMod"
            )


        except:

            pass



    async def is_whitelisted(
        self,
        message
    ):


        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT user_id, role_id
            FROM automod_whitelist
            WHERE guild_id=?
            """,
            (message.guild.id,)
        )


        data = cursor.fetchall()

        conn.close()



        for user_id, role_id in data:


            if user_id == message.author.id:

                return True


            if role_id:

                if any(
                    role.id == role_id
                    for role in message.author.roles
                ):

                    return True



        return False




    async def contains_bad_word(
        self,
        message
    ):


        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT word
            FROM bad_words
            WHERE guild_id=?
            """,
            (message.guild.id,)
        )


        words = cursor.fetchall()

        conn.close()



        text = message.content.lower()



        for word in words:

            if word[0].lower() in text:

                return True



        return False




    @commands.Cog.listener()
    async def on_message(
        self,
        message
    ):


        if not message.guild:
            return


        if message.author.bot:
            return



        # admin bypass

        if message.author.guild_permissions.administrator:

            return



        if await self.is_whitelisted(message):

            return



        anti_spam, anti_links, anti_caps = await self.get_settings(
            message.guild.id
        )


        content = message.content.lower()



        # ======================
        # BLACKLISTA
        # ======================


        if await self.contains_bad_word(message):


            try:

                await message.delete()


                await self.add_warn(
                    message.guild,
                    message.author,
                    "AutoMod: Zakazane słowo"
                )


                await message.channel.send(
                    f"⚠️ {message.author.mention}\n"
                    "Zakazane słowo.",
                    delete_after=5
                )


            except:

                pass


            return




        # ======================
        # ANTISPAM
        # ======================


        if anti_spam:


            key = (
                message.guild.id,
                message.author.id
            )


            now = time.time()


            msgs = self.message_cache.get(
                key,
                []
            )


            msgs.append(now)


            msgs = [
                x for x in msgs
                if now-x < 5
            ]


            self.message_cache[key] = msgs



            if len(msgs) >= 5:


                try:

                    await message.channel.purge(
                        limit=5,
                        check=lambda m:
                        m.author.id == message.author.id
                    )


                    await self.add_warn(
                        message.guild,
                        message.author,
                        "AutoMod: Spam"
                    )


                    await self.timeout_user(
                        message.author
                    )


                    self.message_cache[key] = []


                    await message.channel.send(
                        f"⚠️ {message.author.mention}\n"
                        "Spam wykryty.\n"
                        "+1 warn + timeout 2 min.",
                        delete_after=5
                    )


                except:

                    pass


                return




        # ======================
        # ANTILINK
        # ======================


        if anti_links:


            blocked = [

                "http://",
                "https://",
                "www.",
                "discord.gg/"

            ]



            if any(
                x in content
                for x in blocked
            ):


                try:

                    await message.delete()


                    await self.add_warn(
                        message.guild,
                        message.author,
                        "AutoMod: Link"
                    )


                    await message.channel.send(
                        f"⚠️ {message.author.mention}\n"
                        "Linki są zablokowane.",
                        delete_after=5
                    )


                except:

                    pass


                return





        # ======================
        # ANTICAPS
        # ======================


        if anti_caps:


            letters = [
                c for c in message.content
                if c.isalpha()
            ]


            if len(letters) >= 10:


                upper = sum(
                    1
                    for c in letters
                    if c.isupper()
                )


                if upper / len(letters) >= 0.7:


                    try:

                        await message.delete()


                        await self.add_warn(
                            message.guild,
                            message.author,
                            "AutoMod: Caps"
                        )


                        await message.channel.send(
                            f"⚠️ {message.author.mention}\n"
                            "Nie pisz całych wiadomości capslockiem.",
                            delete_after=5
                        )


                    except:

                        pass



async def setup(bot):

    await bot.add_cog(
        AutoMod(bot)
    )