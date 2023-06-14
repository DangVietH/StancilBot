import discord
from discord import app_commands
from discord.ext import commands
import datetime
from core import Stancil
from cogs.info.help import CustomHelp
from typing import Optional


class Info(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot
        bot.help_command = CustomHelp()
        bot.help_command.cog = self

    @property
    def emoji(self):
        return "ℹ️"

    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context):
        """Show Bot Latency"""
        await ctx.send(f"🏓**Pong!** My latency is {round(self.bot.latency * 1000)}ms")

    @commands.hybrid_command()
    async def uptime(self, ctx: commands.Context):
        """Show Bot Uptime"""
        await ctx.send(f"<t:{int(datetime.datetime.timestamp(self.bot.uptime))}:R>")

    @commands.hybrid_command()
    @app_commands.describe(member="Choose member")
    async def whois(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Display member info"""
        member = member or ctx.author
        if member.activity is not None:
            activity = member.activity.name
        else:
            activity = None

        embed = discord.Embed(timestamp=ctx.message.created_at, color=member.color)
        embed.set_author(name=f"{member.display_name}", icon_url=member.display_avatar.url)
        embed.add_field(name="Nickname", value=member.nick, inline=False)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Status", value=member.status)
        embed.add_field(name="In voice", value=None if not member.voice else member.voice.channel)
        embed.add_field(name="Activity", value=activity)
        embed.add_field(name="Top role", value=member.top_role.mention)
        embed.add_field(name="Bot", value=member.bot)
        embed.add_field(name="Create at", value=f"<t:{int(member.created_at.timestamp())}:R>")
        embed.add_field(name="Join at", value=f"<t:{int(member.joined_at.timestamp())}:R>")
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def serverinfo(self, ctx: commands.Context):
        """Show server information"""
        role_count = len(ctx.guild.roles)
        emoji_count = len(ctx.guild.emojis)
        embed = discord.Embed(title=f"{ctx.guild.name}", timestamp=ctx.message.created_at)
        embed.add_field(name="ID", value=f"{ctx.guild.id}")
        embed.add_field(name="Owner", value=f"{ctx.guild.owner}")
        embed.add_field(name="Member count", value=f"{ctx.guild.member_count}")
        embed.add_field(name="Verification Level", value=f"{ctx.guild.verification_level}")
        embed.add_field(name="Highest role", value=f"{ctx.guild.roles[-1]}")
        embed.add_field(name="Number of roles", value=f"{role_count}")
        embed.add_field(name="Number of emojis", value=f"{emoji_count}")
        embed.add_field(name="Create on", value=f"<t:{int(ctx.guild.created_at.timestamp())}:R>")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def about(self, ctx: commands.Context):
        """Bot information"""
        amount_of_bots = []
        for x in self.bot.users:
            if x.bot:
                amount_of_bots.append(x)
        embed = discord.Embed(title="Bot Information")
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(name="Developer", value=f"DvH#9980")
        embed.add_field(name="Version", value="v0.0.1-alpha")
        embed.add_field(name="Written in", value="Python 3.10.0")
        embed.add_field(name="Library",
                        value=f"[discord.py {discord.__version__}](https://github.com/Rapptz/discord.py)")
        embed.add_field(name="Uptime", value=f"<t:{int(datetime.datetime.timestamp(self.bot.uptime))}:R>")
        embed.add_field(name="Create at", value=f"<t:{int(self.bot.user.created_at.timestamp())}:R>")
        embed.add_field(name="Command's", value=f"{len(self.bot.commands)}")
        embed.add_field(name="Server's", value=f"{len(self.bot.guilds)}")
        embed.add_field(name="User's", value=f"{len(self.bot.users)} total\n{len(amount_of_bots)} bots")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='Invite', url=self.bot.invite))
        view.add_item(discord.ui.Button(label='Support server', url=self.bot.support_server))
        await ctx.send(embed=embed, view=view)
