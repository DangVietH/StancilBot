import discord
from discord.ext import commands
from core import Stancil


class Role(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot:
            return

        data = await self.bot.db.fetchrow(
            "SELECT * FROM role WHERE message=$1",
            payload.message_id
        )
        if not data:
            return
        if data['button']:
            return

        emojis = await self.bot.db.fetchval(
                "SELECT emojis FROM role WHERE message=$1",
                payload.message_id
        )
        roles = await self.bot.db.fetchval(
                "SELECT roles FROM role WHERE message=$1",
                payload.message_id
        )

        guild = self.bot.get_guild(payload.guild_id)

        for i in range(len(emojis)):
            if str(payload.emoji) == emojis[i]:
                role = guild.get_role(int(roles[i]))
                await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot:
            return

        data = await self.bot.db.fetchrow(
            "SELECT * FROM role WHERE message=$1",
            payload.message_id
        )
        if not data:
            return
        if data['button']:
            return

        emojis = await self.bot.db.fetchval(
            "SELECT emojis FROM role WHERE message=$1",
            payload.message_id
        )
        roles = await self.bot.db.fetchval(
            "SELECT roles FROM role WHERE message=$1",
            payload.message_id
        )

        guild = self.bot.get_guild(payload.guild_id)

        for i in range(len(emojis)):
            if str(payload.emoji) == emojis[i]:
                role = guild.get_role(int(roles[i]))
                await payload.member.remove_roles(role)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        stats = await self.bot.db.execute(
            "DELETE FROM role WHERE message=$1",
            payload.message_id,
        )
        if stats == 'DELETE 0':
            return


async def setup(bot: Stancil):
    await bot.add_cog(Role(bot))

