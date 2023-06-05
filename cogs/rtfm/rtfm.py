import warnings
import discord
from discord.ext import commands, menus
from core import Stancil
import cogs.rtfm.rtfm_utils as rtfm
from utilities import MenuPages

# Directly taken from BruceCodesGithub/OG-Robocord, which is Unlicense
# https://github.com/BruceCodesGithub/OG-Robocord/blob/main/cogs/rtfm.py


class RtfmPageSource(menus.ListPageSource):
    def __init__(self, term, docs, data):
        self.term = term
        self.docs = docs
        super().__init__(data, per_page=10)

    async def format_page(self, menu: MenuPages, entries: list):
        embed = discord.Embed(color=discord.Color.green(), title=f"Best matches I can find for {self.term} in {self.docs}")
        embed.description = "\n".join([f"[`{name}`]({value})" for name, value in entries])
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class RtfmListPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu: MenuPages, entries: list):
        embed = discord.Embed(color=discord.Color.green(), title="List of available docs")
        embed.description = "\n".join([f"[`{target}`]({link}): {aliases}" for target, link, aliases in entries])
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class RTFM(commands.Cog):
    emoji = "📚"

    def __init__(self, bot: Stancil):
        self.bot = bot
        self.targets = {
            "python": "https://docs.python.org/3",
            "discord.py": "https://discordpy.readthedocs.io/en/latest/",
            "asyncpg": "https://magicstack.github.io/asyncpg/current/",
        }
        self.aliases = {
            ("py", "py3", "python3", "python"): "python",
            ("dpy", "discord.py", "d.py"): "discord.py",
            ("acpg", "asyncpg"): "asyncpg",
        }
        self.cache = {}

    async def build(self, target) -> None:
        url = self.targets[target]
        req = await self.bot.session.get(url + "/objects.inv")
        if req.status != 200:
            warnings.warn(
                Warning(
                    f"Received response with status code {req.status} when trying to build RTFM cache for {target} through {url}/objects.inv"
                )
            )
            raise commands.CommandError("Failed to build RTFM cache")
        self.cache[target] = rtfm.SphinxObjectFileReader(
            await req.read()
        ).parse_object_inv(url)

    @commands.group(aliases=["rtfd"], invoke_without_command=True, case_insensitive=True)
    async def rtfm(self, ctx: commands.Context, docs: str, *, term: str = None):
        """Search a term in a document. Use rtfm list to find the list of available docs"""
        docs = docs.lower()
        target = None
        for aliases, target_name in self.aliases.items():
            if docs in aliases:
                target = target_name

        if not target:
            return await ctx.reply(
                embed=discord.Embed(
                    title="Invalid Documentation",
                    description=f"Documentation {docs} is invalid. If you want to find valid ones, do {ctx.prefix}rtfm list",
                    color=discord.Color.red()
                )
            )
        if not term:
            return await ctx.reply(self.targets[target])

        cache = self.cache.get(target)
        if not cache:
            await ctx.channel.typing()
            await self.build(target)
            cache = self.cache.get(target)

        results = rtfm.finder(
            term, list(cache.items()), key=lambda x: x[0], lazy=False
        )

        if not results:
            return await ctx.reply(
                f"No results found when searching for {term} in {docs}"
            )

        page = MenuPages(RtfmPageSource(term, docs, results), ctx)
        await page.start()

    @rtfm.command(name="list")
    async def rtfmlist(self, ctx: commands.Context):
        aliases = {v: k for k, v in self.aliases.items()}
        embed = discord.Embed(title="List of available docs", color=discord.Color.green())
        embed.description = "\n".join(
            [
                "[{0}]({1}): {2}".format(
                    target,
                    link,
                    "\u2800".join([f"`{i}`" for i in aliases[target] if i != target]),
                )
                for target, link in self.targets.items()
            ]
        )
        await ctx.send(embed=embed)