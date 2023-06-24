import discord
from discord.ext import commands
from core import Stancil


class Level(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot:
            return

        guild_data = await self.bot.db.fetchrow(
            "SELECT * FROM level_config WHERE guild=$1",
            message.guild.id,
        )
        if not guild_data:
            return

        if message.channel.id in await self.bot.db.fetchval(
                "SELECT ignore_channel FROM level_config WHERE guild = $1",
                message.guild.id
        ):
            return

        data = await self.bot.db.fetchrow(
            "SELECT * FROM leveling WHERE guild=$1 AND member=$2",
            message.guild.id,
            message.author.id
        )

        if not data:
            return await self.bot.db.execute(
                "INSERT INTO leveling(guild, member, level, xp) VALUES($1, $2, $3, $4)",
                message.guild.id,
                message.author.id,
                0,
                guild_data['xp']
            )

        xp = data['xp']
        lvl = 0

        await self.bot.db.execute(
            "UPDATE leveling SET xp = $1 WHERE guild = $2 AND member = $3",
            xp + guild_data['xp'],
            message.guild.id,
            message.author.id
        )

        # level up

        while True:
            if xp < ((100 / 2 * (lvl ** 2)) + (100 / 2 * lvl)):
                break
            lvl += 1

        xp -= ((100 / 2 * ((lvl - 1) ** 2)) + (100 / 2 * (lvl - 1)))

        if data['level'] < lvl:
            await self.bot.db.execute(
                "UPDATE leveling SET level = $1 WHERE guild = $2 AND member = $3",
                data['level'] + 1,
                message.guild.id,
                message.author.id
            )

            if guild_data['lvl_up_channel'] is None:
                channel = message.channel
            else:
                channel = self.bot.get_channel(guild_data['lvl_up_channel'])

            level_up_msg = guild_data['lvl_up_text'] or "🎉 {mention} has reached level **{level}**!!🎉"
            await channel.send(level_up_msg.format(
                mention=message.author.mention,
                name=message.author.display_name,
                server=message.guild.name,
                username=message.author.name,
                level=data['level'] + 1,
                xp=data['xp']
            ))

            role_level = await self.bot.db.fetchval(
                "SELECT role_level FROM level_config WHERE guild = $1",
                message.guild.id
            )
            role_id = await self.bot.db.fetchval(
                "SELECT role_id FROM level_config WHERE guild = $1",
                message.guild.id
            )

            for i in range(len(role_id)):
                if lvl == int(role_level[i]):
                    role = message.guild.get_role(int(role_id[i]))
                    await message.author.add_roles(role)
                    await channel.send(f"{message.author.mention} also receive `{role.name}` role")


async def setup(bot: Stancil):
    await bot.add_cog(Level(bot))
