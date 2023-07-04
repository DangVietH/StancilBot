import discord
from discord.ext import commands
from core import Stancil


class GuildEvents(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.bot.db.execute(
            """
            INSERT INTO server(id, prefix, mute_role, config_role, mod_role, ban_message) 
            VALUES($1, $2, $3, $4, $5, $6)
            """,
            guild.id,
            None,
            None,
            None,
            None,
            None
        )

    @commands.Cog.listener()
    async def on_guild_leave(self, guild: discord.Guild):
        await self.bot.db.execute(
            "DELETE FROM server WHERE id=$1",
            guild.id
        )
        await self.bot.db.execute(
            "DELETE FROM tag WHERE guild=$1",
            guild.id
        )
        await self.bot.db.execute(
            "DELETE FROM leveling WHERE guild=$1",
            guild.id
        )
        await self.bot.db.execute(
            "DELETE FROM starboard_config WHERE guild=$1",
            guild.id
        )
        await self.bot.db.execute(
            "DELETE FROM starboard_message WHERE guild=$1",
            guild.id
        )
        await self.bot.db.execute(
            "DELETE FROM role WHERE guild=$1",
            guild.id
        )


async def setup(bot: Stancil):
    await bot.add_cog(GuildEvents(bot))
