import discord
from discord.ext import commands, menus
import datetime
from utilities import time_converter
from utilities import DefaultPageSource, MenuPages


class LyricPageSource(menus.ListPageSource):
    def __init__(self, title, url, thumbnail, data):
        self.title = title
        self.url = url
        self.thumbnail = thumbnail
        super().__init__(data, per_page=20)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, url=self.url)
        embed.description = "\n".join([part for part in entries])
        embed.set_thumbnail(url=self.thumbnail)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def emoji(self):
        return "📝"

    @commands.group(invoke_without_command=True, case_insensitive=True, aliases=['reminder'])
    async def remindme(self, ctx: commands.Context, time, *, reminder):
        """Set your reminder. Time format includes: s, m, h, d"""

        converted_time = time_converter(time)
        if converted_time == -1:
            return await ctx.send("You didn't format the time correctly. Example of a correct one: `4h`")
        if converted_time == -2:
            return await ctx.send("Time must be an integer. Example of a correct one: `4h`")

        final_time = datetime.datetime.now() + datetime.timedelta(seconds=converted_time)
        await self.bot.db.execute(
            "INSERT INTO remindme(id, users, end_time, reminder) VALUES($1, $2, $3, $4)",
            ctx.message.id,
            ctx.author.id,
            final_time,
            reminder
        )
        await ctx.send(f"⏰ Reminder set! Reminder id: `{ctx.message.id}`")

    @remindme.command(name="delete")
    async def remindme_delete(self, ctx: commands.Context, reminder_id: int):
        """Delete your reminder"""
        data = await self.bot.db.fetchrow(
            "SELECT * FROM remindme WHERE id=$1 AND users=$2",
            reminder_id,
            ctx.author.id
        )
        if not data:
            return await ctx.send("That reminder doesn't exist")

        await self.bot.db.execute("DELETE FROM remindme WHERE id=$1", reminder_id)
        await ctx.send("Reminder deleted")

    @remindme.command(name="list")
    async def remindme_list(self, ctx: commands.Context):
        """Show the list of reminders you have"""
        data = await self.bot.db.fetch(
            "SELECT * FROM remindme WHERE users=$1",
            ctx.author.id
        )
        if not data:
            return await ctx.send("You have no reminder")

        menu_data = []
        for reminders in data:
            menu_data.append((
                f"ID - {reminders['id']}",
                f"**End at:** <t:{int(datetime.datetime.timestamp(reminders['end_time']))}:R>"
            ))

        page = MenuPages(DefaultPageSource(f"Your Reminder", menu_data), ctx)
        await page.start()

    @commands.command(aliases=['lyrc', 'lyric'])
    async def lyrics(self, ctx, *, song):
        """Show the lyrics of a song"""
        await ctx.channel.typing()
        resp = await self.bot.session.get(
            f"https://some-random-api.com/others/lyrics", params={"title": song}
        )
        data = await resp.json()

        if data.get('error'):
            return await ctx.send(f"Error: {data['error']}")

        pag_data = []
        for chunk in data['lyrics'].split('\n'):
            pag_data.append(chunk)
        page = MenuPages(
            LyricPageSource(data['title'], data['links']['genius'], data['thumbnail']['genius'], pag_data),
            ctx)
        await page.start()
