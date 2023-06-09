import discord
from discord.ext import commands
from core import Stancil


class Owner(commands.Cog):
    """Only DvH can use it"""

    def __init__(self, bot: Stancil):
        self.bot = bot

    @property
    def emoji(self):
        return "👑"

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def load(self, ctx: commands.Context, *, cog=None):
        """Load a cog"""
        try:
            await self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'⬆️`{cog}`')

    @commands.command()
    async def unload(self, ctx: commands.Context, *, cog=None):
        """Unload a cog"""
        try:
            await self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'⬇️`{cog}`')

    @commands.command()
    async def reload(self, ctx: commands.Context, *, cog=None):
        """Reload a cog"""
        try:
            if cog == "all":
                for ext in self.bot.coglist:
                    await self.bot.reload_extension(ext)
            else:
                await self.bot.reload_extension(cog)
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'🔁`{cog}`')

    @commands.command()
    async def setstatus(self, ctx: commands.Context, presence, *, msg):
        """Change bot status"""
        if presence == "game":
            await self.bot.change_presence(
                activity=discord.Game(name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users))))
        if presence == "watch":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                     name=str(msg).format(server=len(self.bot.guilds),
                                                                                          user=len(self.bot.users))))
        if presence == "listen":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
                                                                     name=str(msg).format(server=len(self.bot.guilds),
                                                                                          user=len(self.bot.users))))
        if presence == "stream":
            await self.bot.change_presence(
                activity=discord.Streaming(name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users)),
                                           url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        else:
            await ctx.send('Invalid status')
        await ctx.message.add_reaction('👌')

    @commands.command()
    async def sync(self, ctx: commands.Context, *, current_guild=None):
        """Sync application commands"""
        if current_guild is None or current_guild.lower() == "n":
            slash_list = await self.bot.tree.sync(guild=None)
        elif current_guild.lower() == "y":
            self.bot.tree.copy_global_to(guild=ctx.guild)
            slash_list = await self.bot.tree.sync(guild=ctx.guild)
        else:
            return await ctx.send("Incorrect value. There's only `y` and `n`")

        await ctx.send(f'Successfully synced {len(slash_list)} commands')

    @commands.command()
    async def cmd_toggle(self, ctx: commands.Context, *, command: str):
        """Toggle a command on and off"""
        command = self.bot.get_command(command)
        if not command.enabled:
            command.enabled = True
            await ctx.reply(F"Enabled {command.name} command")
        else:
            command.enabled = False
            await ctx.reply(F"Disabled {command.name} command.")

    @commands.command()
    async def shutdown(self, ctx: commands.Context):
        """Shut down the bot"""
        await ctx.send('Shutting down...')
        await self.bot.db.close()
        await self.bot.session.close()
        await self.bot.close()
