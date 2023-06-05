import discord
from discord.ext import commands, tasks
from core import Stancil
import datetime


class Timers(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot
        self.time_checker.start()

    async def cog_unload(self):
        self.time_checker.cancel()

    @tasks.loop(seconds=2)
    async def time_checker(self):
        timer_data = await self.bot.db.fetch("SELECT * FROM remindme")
        current_time = datetime.datetime.now()
        for data in timer_data:
            if current_time >= data['end_time']:
                user = self.bot.get_user(data['users'])
                if not user:
                    return await self.bot.db.execute("DELETE FROM remindme WHERE id=$1", data['id'])
                await user.send(f"**Reminder:** {data['reminder']}")
                await self.bot.db.execute("DELETE FROM remindme WHERE id=$1", data['id'])


async def setup(bot: Stancil):
    await bot.add_cog(Timers(bot))
