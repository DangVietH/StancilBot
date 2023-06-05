import discord
from discord.ext import commands
import os
import asyncpg
import aiohttp
import re

# jishaku configs
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ['JISHAKU_RETAIN'] = "True"
os.environ['JISHAKU_FORCE_PAGINATOR'] = "True"

# cog list
coglist = [
    'cogs.config',
    'cogs.entertainment',
    'cogs.info',
    'cogs.leveling',
    'cogs.moderation',
    'cogs.owner',
    'cogs.rtfm',
    'cogs.utils',
    'events.guild_events',
    'events.level',
    'events.on_error',
    'events.starboard',
    'events.timers',
    'jishaku'
]


class Stancil(commands.Bot):
    db: asyncpg.Pool

    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix,
            intents=discord.Intents.all(),
            strip_after_prefix=True,
            case_insensitive=True,
            owner_id=860876181036335104,
            activity=discord.Game(name="s!help"),
        )

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()

        # loading cogs
        for ext in coglist:
            try:
                await self.load_extension(ext)
                print(f"{ext} loaded")
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()
        print(f"{self.user} is online!")

    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        if re.fullmatch(rf"<@!?{self.user.id}>", message.content):
            data = await self.db.fetchrow(
                "SELECT * FROM server WHERE id=$1",
                message.guild.id
            )

            if data['prefix'] is None:
                return await message.channel.send(f"**Prefix:** `s!`")
            return await message.channel.send(f"**Prefix:** `{data['prefix']}`")

        await self.process_commands(message)

    async def get_prefix(self, message: discord.Message):
        data = await self.db.fetchval(
            "SELECT prefix FROM server WHERE id=$1",
            message.guild.id
        )

        if data is None:
            prefix = "s!"
        else:
            prefix = data
        return commands.when_mentioned_or(prefix)(self, message)
