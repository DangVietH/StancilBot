import discord
from discord.ext import commands
from core import Stancil
from utilities import time_converter
import datetime


def has_mod_role():
    """Check does the user has config role"""
    async def predicate(ctx: commands.Context):
        data = ctx.bot.db.fetchval(
            "SELECT mod_role FROM server WHERE id = $1",
            ctx.guild.id
        )
        if not data:
            return False
        elif ctx.guild.get_role(data) in ctx.author.roles:
            return True

    return commands.check(predicate)


class Moderation(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(moderate_members=True))
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        """Warn a Member"""
        embed = discord.Embed(
            description=f"You have been warned in **{ctx.guild.name}** for: **{reason}**",
            color=discord.Color.red()
        )
        await member.send(embed=embed)
        await ctx.send(f"Successfully warned {member.mention} for `{reason}`")

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(moderate_members=True))
    async def timeout(self, ctx: commands.Context, member: discord.Member, time, *, reason=None):
        """Timeout a member"""
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't timeout someone with a higher role than you")
        converted_time = time_converter(time)
        if converted_time == -1:
            return await ctx.send("You didn't format the time correctly. Example of a correct one: `4h`")
        if converted_time == -2:
            return await ctx.send("Time must be an integer. Example of a correct one: `4h`")
        duration = datetime.timedelta(minutes=converted_time)
        await member.timeout(duration, reason=reason)

        await member.send(f"You were timeout in **{ctx.guild.name}** for **{reason}**")
        await ctx.send(f"Successfully timeout {member.mention} for `{reason}`")

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(moderate_members=True))
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        """Untimeout a member"""
        await member.edit(timed_out_until=None)
        await member.send(f"You were untimeout in **{ctx.guild.name}** for **{reason}**")
        await ctx.send(f"Successfully untimeout {member.mention} for `{reason}`")

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(kick_members=True))
    async def mute(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        """Mute a member"""
        mute_role_id = await self.bot.db.fetchval("SELECT mute_role FROM server WHERE id=$1", ctx.guild.id)
        mute_role = ctx.guild.get_role(mute_role_id)
        await member.add_roles(mute_role, reason=reason)
        await ctx.send(f"{member.mention} has been muted for `{reason}`")
        await member.send(f"You were muted in **{ctx.guild.name}** for `{reason}`")

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(kick_members=True))
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        """Unmute a member"""
        mute_role_id = await self.bot.db.fetchval("SELECT mute_role FROM server WHERE id=$1", ctx.guild.id)
        mute_role = ctx.guild.get_role(mute_role_id)
        await member.remove_roles(mute_role, reason=reason)
        await ctx.send(f"{member.mention} has been unmuted for `{reason}`")
        await member.send(f"You were unmuted in **{ctx.guild.name}** for `{reason}`")

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(kick_members=True))
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        """Kick a member"""
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't kick someone with a higher role than you")
        if not member.bot:
            await member.send(f"You've been kick from **{ctx.guild.name}** for **{reason}**")
        await member.kick(reason=reason)
        await ctx.send(f"Successfully kick **{member}** for `{reason}")

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(ban_members=True))
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        """Ban a member"""
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't kick someone with a higher role than you")
        if not member.bot:
            ban_message = await self.bot.db.fetchval("SELECT ban_message FROM server WHERE id=$1", ctx.guild.id)
            await member.send(ban_message or f"You've been **BANNED** from **{ctx.guild.name}** for **{reason}**")
        await member.ban(reason=reason)
        await ctx.send(f"Successfully banned **{member}** for `{reason}")

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(ban_members=True))
    async def unban(self, ctx: commands.Context, member: discord.BanEntry, *, reason=None):
        """Unban someone. To make this command work, pass the ID of the banned member"""
        await ctx.guild.unban(member.user, reason=reason)
        await ctx.send(f"Successfully unban {member.user} for `{reason}`")

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Lock a channel"""
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send('🔒 Channel locked.')

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Unlock a channel"""
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send('🔓 Channel unlocked.')

    @commands.command()
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_messages=True))
    async def purge(self, ctx: commands.Context, amount: int = 1):
        """Purge messages"""
        await ctx.channel.purge(limit=amount + 1)

