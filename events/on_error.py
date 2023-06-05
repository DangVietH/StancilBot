import discord
from discord.ext import commands
from core import Stancil
import datetime


class OnError(commands.Cog):
    def __int__(self, bot: Stancil):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        ignore = (commands.CommandNotFound, discord.NotFound, discord.Forbidden)

        if isinstance(error, ignore):
            return

        embed = discord.Embed(color=discord.Color.red())

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(
                [f"{x.replace('_', ' ').replace('guild', 'server').title()}" for x in error.missing_permissions])
            embed.title = "Bot Missing Permissions"
            embed.description = f"I am missing the following permissions: {perms}!"

        elif isinstance(error, commands.MissingPermissions):
            embed.title = "Missing Permissions"
            embed.description = f"You have no permissions to run this command!"

        elif isinstance(error, commands.NotOwner):
            embed.title = "Not Owner"
            embed.description = f"You're not the owner of this bot!"

        elif isinstance(error, commands.MissingRequiredArgument):
            embed.title = "Missing Argument"
            embed.description = f"You are missing a required argument for this command to work: `{error.param.name}`!"

        elif isinstance(error, commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            wait_until_finish = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            embed.title = "Command on Cooldown"
            embed.description = f'⏱️ You can use this command after <t:{int(datetime.datetime.timestamp(wait_until_finish))}:R>'

        elif isinstance(error, commands.DisabledCommand):
            embed.title = "Disabled"
            embed.description = "This command is disabled by the bot's owner!"

        elif isinstance(error, commands.BadArgument):
            if isinstance(error, commands.MessageNotFound):
                embed.title = "Message Not Found"
                embed.description = "The message id/link you provided is invalid or deleted!"

            if isinstance(error, commands.MemberNotFound):
                embed.title = "Member Not Found"
                embed.description = "The member id/mention/name you provided is invalid or didn't exist in this server!"

            if isinstance(error, commands.UserNotFound):
                embed.title = "User Not Found"
                embed.description = "The user id/mention/name you provided is invalid or I can't see that User!"

            if isinstance(error, commands.ChannelNotFound):
                embed.title = "Channel Not Found"
                embed.description = "The channel id/mention/name you provided is invalid or I can't access it!"

            if isinstance(error, commands.RoleNotFound):
                embed.title = "Role Not Found"
                embed.description = "The role id/mention/name you provided is invalid or I cannot see that role!"

            if isinstance(error, commands.EmojiNotFound):
                embed.title = "Emoji Not Found"
                embed.description = "The emoji id/name you provided is invalid or I cannot see that emoji!"

        else:
            embed.title = "Unexpected Error"
            embed.description = error

        await ctx.send(embed=embed)


async def setup(bot: Stancil):
    await bot.add_cog(OnError(bot))

