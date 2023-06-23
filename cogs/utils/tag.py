import discord
from discord.ext import commands
from core import Stancil
import datetime
from utilities import DefaultPageSource, MenuPages, SecondPageSource


class Tag(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot

    @property
    def emoji(self):
        return "🏷️"

    @commands.group(invoke_without_command=True, case_insensitive=True, aliases=['tags'])
    async def tag(self, ctx: commands.Context, *, tag_name=None):
        """Find a tag. Remember tags are CASE SENSITIVE"""
        if tag_name is None:
            return await ctx.send_help(ctx.command)

        data = await self.bot.db.fetchrow(
            "SELECT * FROM tag WHERE name=$1 AND guild=$2",
            tag_name,
            ctx.guild.id
        )

        if not data:
            return await ctx.send("Tag Not Found. Remember tags are CASE SENSITIVE")

        await ctx.send(data['content'])
        await self.bot.db.execute(
            "UPDATE tag SET stats = $1 WHERE name=$2 AND guild=$3",
            1 + data['stats'],
            tag_name,
            ctx.guild.id
        )

    @tag.command(name="create")
    async def tag_create(self, ctx: commands.Context):
        """Create a tag"""

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        msg = await ctx.send("What is the tag name?")
        name_value = await self.bot.wait_for('message', check=check)
        if await self.bot.db.fetchrow("SELECT * FROM tag WHERE name=$1 AND guild=$2",
                                      name_value.content,
                                      ctx.guild.id
                                      ):
            await ctx.channel.purge(limit=1)
            await msg.edit(content="Tag with that name already exist. Remember tag names are CASE SENSITIVE")
            return
        await ctx.channel.purge(limit=1)

        await msg.edit(content="What is the tag content?")
        content_value = await self.bot.wait_for('message', check=check)
        await ctx.channel.purge(limit=1)

        await self.bot.db.execute(
            "INSERT INTO tag(name, content, owner, guild, stats, create_at) VALUES($1, $2, $3, $4, $5, $6)",
            name_value.content,
            content_value.content,
            ctx.author.id,
            ctx.guild.id,
            0,
            datetime.datetime.now()
        )
        await msg.edit(content=f"Tag `{name_value.content}` successfully create")

    @tag.command(name="delete")
    async def tag_delete(self, ctx: commands.Context, *, tag_name):
        """Delete a tag"""
        data = await self.bot.db.fetchrow(
            "SELECT * FROM tag WHERE name=$1 AND guild=$2 AND owner=$3",
            tag_name,
            ctx.guild.id,
            ctx.author.id
        )

        if not data:
            return await ctx.send("Tag not found. Either tag doesn't exist or you're not the owner of the tag. Remember, tags are CASE SENSITIVE")

        await self.bot.db.execute(
            "DELETE FROM tag WHERE name=$1 AND guild=$2 AND owner=$3",
            tag_name,
            ctx.guild.id,
            ctx.author.id
        )
        await ctx.send("Tag successfully deleted")

    @tag.command(name="edit")
    async def tag_edit(self, ctx: commands.Context, *, tag_name):
        """Edit a tag"""
        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        data = await self.bot.db.fetchrow(
            "SELECT * FROM tag WHERE name=$1 AND guild=$2 AND owner=$3",
            tag_name,
            ctx.guild.id,
            ctx.author.id
        )

        if not data:
            return await ctx.send("Tag not found. Either tag doesn't exist or you're not the owner of the tag. Remember, tags are CASE SENSITIVE")

        msg = await ctx.send("What will be the tag content?")
        edit_value = await self.bot.wait_for('message', check=check)
        await ctx.channel.purge(limit=1)

        await self.bot.db.execute(
            "UPDATE tag SET content = $1 WHERE name=$2 AND guild=$3 AND owner=$4",
            edit_value.content,
            tag_name,
            ctx.guild.id,
            ctx.author.id
        )
        await msg.edit(content=f"Tag `{tag_name}` successfully edited")

    @tag.command(name="info")
    async def tag_info(self, ctx: commands.Context, *, tag_name):
        """Show info of a tag"""
        data = await self.bot.db.fetchrow(
            "SELECT * FROM tag WHERE name=$1 AND guild=$2",
            tag_name,
            ctx.guild.id
        )

        if not data:
            return await ctx.send("Tag Not Found. Remember tags are CASE SENSITIVE")
        embed = discord.Embed(title=f"{tag_name} Info")
        embed.add_field(name="Owner", value=ctx.guild.get_member(data['owner']).display_name)
        embed.add_field(name="Usage", value=data['stats'])
        embed.add_field(name="Create at", value=f"<t:{int(datetime.datetime.timestamp(data['create_at']))}>")
        await ctx.send(embed=embed)

    @tag.command(name="list")
    async def tag_list(self, ctx: commands.Context):
        """Show the list of tags in this server"""
        data = await self.bot.db.fetch(
            "SELECT * FROM tag WHERE guild=$1 ORDER BY name", ctx.guild.id
        )

        menu_data = []
        num = 0
        for d in data:
            num += 1
            menu_data.append(
                (
                    num,
                    d['name']
                )
            )

        page = MenuPages(SecondPageSource(f"{ctx.guild.name} Tags", menu_data), ctx)
        await page.start()

    @tag.command(name="userlist")
    async def tag_userlist(self, ctx: commands.Context, member: discord.Member = None):
        """Show the list of tags owned by someone"""
        member = member or ctx.author
        data = await self.bot.db.fetch(
            "SELECT * FROM tag WHERE guild=$1 AND owner=$2 ORDER BY name", ctx.guild.id, member.id
        )

        menu_data = []
        num = 0
        for d in data:
            num += 1
            menu_data.append(
                (
                    num,
                    d['name']
                )
            )

        page = MenuPages(SecondPageSource(f"{member.display_name} Tags", menu_data), ctx)
        await page.start()

    @tag.command(name="leaderboard")
    async def tag_leaderboard(self, ctx: commands.Context):
        """Show the list of tags rank by usage"""
        data = await self.bot.db.fetch(
            "SELECT * FROM tag WHERE guild=$1 ORDER BY stats", ctx.guild.id
        )

        menu_data = []
        num = 0
        for d in data:
            num += 1
            menu_data.append(
                (
                    f"{num}: {d['name']}",
                    f"Usage: {d['stats']}"
                )
            )

        page = MenuPages(DefaultPageSource(f"{ctx.guild.name} Tag Leaderboard", menu_data), ctx)
        await page.start()
