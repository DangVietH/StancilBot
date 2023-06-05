import discord
from discord.ext import commands
import io
from core import Stancil


class Image(commands.Cog):
    """Image Categories"""
    emoji = "🖼"

    def __init__(self, bot: Stancil):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gay(self, ctx, member: discord.Member = None):
        """Ad an lgbt flag on your avatar border"""
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.com/canvas/lgbt", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"gay.png"
        ))

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def jail(self, ctx, member: discord.Member = None):
        """Ad jail bars overlay over your avatar"""
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.com/canvas/jail", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"jail.png"
        ))

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def triggered(self, ctx, member: discord.Member = None):
        """Ad a triggered flag overlay over your avatar"""
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.com/canvas/triggered", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"triggered.gif"
        ))

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def wasted(self, ctx, member: discord.Member = None):
        """Ad wasted overlay over your avatar"""
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.com/canvas/wasted", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"wasted.png"
        ))

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def comrade(self, ctx, member: discord.Member = None):
        """Ad a soviet flag overlay over your avatar"""
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.com/canvas/comrade", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"comrade.png"
        ))

    @commands.command(aliases=["ytc", "youtube-comment"])
    async def ytcomment(self, ctx, *, comment="Nothing you idiot"):
        """Make a fake youtube comment"""
        resp = await self.bot.session.get(
            f"https://some-random-api.com/canvas/youtube-comment", params={
                "avatar": ctx.author.display_avatar.url,
                "username": ctx.author.name,
                "comment": comment
            }
        )
        await ctx.send(file=discord.File(io.BytesIO(await resp.read()), 'yt.png'))

    @commands.command()
    async def tweet(self, ctx, name, *, comment="Nothing you idiot"):
        """Make a fake tweet"""
        resp = await self.bot.session.get(
            f"https://some-random-api.com/canvas/tweet", params={
                "avatar": ctx.author.display_avatar.url,
                "username": ctx.author.name,
                "displayname": name,
                "comment": comment
            }
        )
        await ctx.send(file=discord.File(io.BytesIO(await resp.read()), 'tweet.png'))