import discord
from discord.ext import commands, tasks
from core import Stancil
import datetime


class Timers(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot
        self.reminder_checker.start()
        self.starboard_expire.start()

    async def cog_unload(self):
        self.reminder_checker.cancel()
        self.starboard_expire.cancel()

    @tasks.loop(seconds=2)
    async def reminder_checker(self):
        reminder_data = await self.bot.db.fetch("SELECT * FROM remindme")
        current_time = datetime.datetime.now()
        for data in reminder_data:
            if current_time >= data['end_time']:
                user = self.bot.get_user(data['users'])
                if not user:
                    return await self.bot.db.execute("DELETE FROM remindme WHERE id=$1", data['id'])
                await user.send(f"**Reminder:** {data['reminder']}")
                await self.bot.db.execute("DELETE FROM remindme WHERE id=$1", data['id'])

    @tasks.loop(seconds=2)
    async def starboard_expire(self):
        sb_data = await self.bot.db.fetch("SELECT * FROM starboard_message")
        current_time = datetime.datetime.now()
        for starboard in sb_data:
            if current_time >= starboard['expire']:
                await self.bot.db.execute(
                    "DELETE FROM starboard_message WHERE message=$1",
                    starboard['message']
                )

async def setup(bot: Stancil):
    await bot.add_cog(Timers(bot))
