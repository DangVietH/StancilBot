import discord
from discord.ext import commands
from core import Stancil


def has_config_role():
    """Check does the user has config role"""
    async def predicate(ctx: commands.Context):
        data = ctx.bot.db.fetchval(
            "SELECT config_role FROM server WHERE id = $1",
            ctx.guild.id
        )
        if not data:
            return False
        elif ctx.guild.get_role(data) in ctx.author.roles:
            return True

    return commands.check(predicate)


class Confirm(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.value = None

    async def interaction_check(self, interaction) -> bool:
        if interaction.user == self.ctx.author:
            return True
        else:
            await interaction.response.send_message("You can't use these buttons", ephemeral=True)
            return False

    @discord.ui.button(label='Enable', style=discord.ButtonStyle.green)
    async def enable(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label='Disable', style=discord.ButtonStyle.red)
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()


class Configuration(commands.Cog):
    """Configuration settings for the bot in this server"""

    def __init__(self, bot: Stancil):
        self.bot = bot

    @property
    def emoji(self):
        return "⚙️"

    @commands.command(name="config-role")
    @commands.has_permissions(manage_guild=True)
    async def config_role(self, ctx: commands.Context, *, role: discord.Role):
        """Setup config role"""
        await self.bot.db.execute(
            "UPDATE server SET config_role = $1 WHERE id = $2",
            role.id,
            ctx.guild.id
        )
        await ctx.send(f"Alright anybody with `{role.name}` can use the configuration commands")

    @commands.command(name="mod-role")
    @commands.has_permissions(manage_guild=True)
    async def mod_role(self, ctx: commands.Context, *, role: discord.Role):
        """Setup mod role"""
        await self.bot.db.execute(
            "UPDATE server SET mod_role = $1 WHERE id = $2",
            role.id,
            ctx.guild.id
        )
        await ctx.send(f"Alright anybody with `{role.name}` can use the moderation commands")

    @commands.command(name="set-prefix")
    @commands.has_permissions(manage_guild=True)
    async def set_prefix(self, ctx: commands.Context, *, custom_prefix):
        """Set custom prefix"""
        await self.bot.db.execute(
            "UPDATE server SET prefix = $1 WHERE id = $2",
            custom_prefix,
            ctx.guild.id
        )
        await ctx.send(f"Server prefix set to `{custom_prefix}`")

    @commands.command(name="reset-prefix")
    @commands.has_permissions(manage_guild=True)
    async def reset_prefix(self, ctx: commands.Context):
        """Reset back to default prefix"""
        await self.bot.db.execute(
            "UPDATE server SET prefix = $1 WHERE id = $2",
            None,
            ctx.guild.id
        )
        await ctx.send("Prefix Reset back to `s!`")

    @commands.command(name="mute-role")
    @commands.has_permissions(manage_roles=True)
    async def mute_role(self, ctx: commands.Context, role: discord.Role):
        await self.bot.db.execute(
            "UPDATE server SET mute_role = $1 WHERE id = $2",
            role.id,
            ctx.guild.id
        )
        await ctx.send(f"Mute role set too `{role.name}`")

    @commands.command(name="ban-message")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_guild=True))
    async def ban_message(self, ctx: commands.Context, *, message):
        """Customize the ban message that will be dm to the member when they got banned"""
        await self.bot.db.execute(
            "UPDATE server SET ban_message = $1 WHERE id = $2",
            message,
            ctx.guild.id
        )
        await ctx.send(f"`{message}` will be sent to the member when they got banned")

    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def level(self, ctx: commands.Context):
        """Configure leveling for your server"""
        data = await self.bot.db.fetchrow("SELECT * FROM level_config WHERE guild=$1", ctx.guild.id)
        if not data:
            return await ctx.send_help(ctx.command)

        ignored_channels = await self.bot.db.fetchval(
            "SELECT level_config FROM starboard_config WHERE guild = $1",
            ctx.guild.id
        )
        ig_c_list = ""
        if not ignored_channels:
            ig_c_list = "None"
        else:
            for c in ignored_channels:
                channel_id = ctx.guild.get_channel(int(c))
                ig_c_list += f"{channel_id.mention}, "
            ig_c_list = ig_c_list[:-2]

        embed = discord.Embed(title="Leveling Configuration for this Server")
        embed.add_field(name="Announcement Channel", value=data['lvl_up_channel'])
        embed.add_field(name="XP per message", value=data['xp'])
        embed.add_field(name="Level up text",
                        value=f"```{data['lvl_up_text'] or '🎉 {mention} has reached level **{level}**!!🎉'}```",
                        inline=False)
        embed.add_field(name="Ignored Channel", value=ig_c_list)
        await ctx.send(embed=embed)

    @level.command(name="enable")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_messages=True))
    async def level_enable(self, ctx: commands.Context):
        """Enable leveling"""
        await self.bot.db.execute(
            """
            INSERT INTO
            level_config(guild, xp, lvl_up_text, lvl_up_channel, ignore_channel, role_level, role_id)
            VALUES($1, $2, $3, $4, $5, $6, $7)
            """,
            ctx.guild.id,
            5,
            None,
            None,
            [],
            [],
            []
        )
        await ctx.send("Leveling is now enabled in this server")

    @level.command(name="disable")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_messages=True))
    async def level_disable(self, ctx: commands.Context):
        """Disable leveling"""
        await self.bot.db.execute(
            "DELETE FROM level_config WHERE guild=$1",
            ctx.guild.id
        )
        await self.bot.db.execute(
            "DELETE FROM leveling WHERE guild=$1",
            ctx.guild.id
        )
        await ctx.send("Leveling is now disabled in this server")

    @level.command(name="xp")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_messages=True))
    async def level_xp(self, ctx: commands.Context, xp: int):
        """Configure the amount of xp when a member send a message"""
        await self.bot.db.execute(
            "UPDATE level_config SET xp = $1 WHERE guild = $2",
            xp,
            ctx.guild.id
        )
        await ctx.send(f"Xp amount set to `{xp}`")

    @level.command(name="text")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_messages=True))
    async def level_text(self, ctx: commands.Context, *, text):
        """Custom level up message.
        Here are the list of variables you can use:
        - {mention}: Mention the member
        - {username}: The username of the Member
        - {name}: The member's name
        - {server}: The server's name
        - {level}: Show member's level
        - {xp}: Show member's xp
        """

        await self.bot.db.execute(
            "UPDATE level_config SET lvl_up_text = $1 WHERE guild = $2",
            text,
            ctx.guild.id
        )
        await ctx.send(f"Level up message updated to ```{text}```")

    @level.command(name="set-channel")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_channels=True))
    async def level_set_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set level up announcement channel"""
        channel = channel or ctx.channel
        await self.bot.db.execute(
            "UPDATE level_config SET lvl_up_channel = $1 WHERE guild = $2",
            channel.id,
            ctx.guild.id
        )
        await ctx.send(f"Level up announcement channel set to {channel.mention}")

    @level.command(name="unset-channel")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_channels=True))
    async def level_unset_channel(self, ctx: commands.Context):
        """Reset back to level up messages responding below member's message"""
        await self.bot.db.execute(
            "UPDATE level_config SET lvl_up_channel = $1 WHERE guild = $2",
            None,
            ctx.guild.id
        )
        await ctx.send("Level up messages will now respond below member's message")

    @level.command(name="add-role-reward")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_roles=True))
    async def add_role_award(self, ctx: commands.Context, level: int, role: discord.Role):
        """Award role when member reach a certain role"""
        if role.id in await self.bot.db.fetchval(
                "SELECT role_id FROM level_config WHERE guild = $1",
                ctx.guild.id
        ):
            return await ctx.send("Role already part of the role reward system")

        await self.bot.db.execute(
            "UPDATE level_config SET role_id = ARRAY_APPEND(role_id, $1) WHERE guild = $2",
            role.id,
            ctx.guild.id
        )
        await self.bot.db.execute(
            "UPDATE level_config SET role_level = ARRAY_APPEND(role_level, $1) WHERE guild = $2",
            level,
            ctx.guild.id
        )
        await ctx.send(f"**{role.name}** role assigned to level **{level}**")

    @level.command(name="remove-role-reward")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_channels=True))
    async def remove_role_award(self, ctx: commands.Context, role: discord.Role):
        """Unignore certain channels from the level system"""
        role_level = await self.bot.db.fetchval(
            "SELECT role_level FROM level_config WHERE guild = $1",
            ctx.guild.id
        )
        role_id = await self.bot.db.fetchval(
            "SELECT role_id FROM level_config WHERE guild = $1",
            ctx.guild.id
        )
        level_data = 0

        for i in range(len(role_level)):
            if role.id == int(role_id[i]):
                level_data = role_level[i]
                break
        await self.bot.db.execute(
            "UPDATE level_config SET role_id = ARRAY_REMOVE(role_id, $1) WHERE guild = $2",
            role.id,
            ctx.guild.id
        )
        await self.bot.db.execute(
            "UPDATE level_config SET role_level = ARRAY_REMOVE(role_level, $1) WHERE guild = $2",
            level_data,
            ctx.guild.id
        )
        await ctx.send(f"{role.name} successfully remove from role reward system")

    @level.command(name="ignore-channel")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_channels=True))
    async def ignore_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        """Ignored certain channels from the level system"""
        if channel.id in await self.bot.db.fetchval(
                "SELECT ignore_channel FROM level_config WHERE guild = $1",
                ctx.guild.id
        ):
            return await ctx.send("Channel already ignored from level system")

        await self.bot.db.execute(
            "UPDATE level_config SET ignore_channel = ARRAY_APPEND(ignore_channel, $1) WHERE guild = $2",
            channel.id,
            ctx.guild.id
        )
        await ctx.send(f"{channel.mention} successfully ignored from the level system")

    @level.command(name="unignore-channel")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_channels=True))
    async def unignore_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        """Unignore certain channels from the level system"""
        await self.bot.db.execute(
            "UPDATE level_config SET ignore_channel = ARRAY_REMOVE(ignore_channel, $1) WHERE guild = $2",
            channel.id,
            ctx.guild.id
        )
        await ctx.send(f"{channel.mention} successfully unignored from the level system")

    @commands.group(invoke_without_command=True, case_insensitive=True, aliases=['sb'])
    async def starboard(self, ctx: commands.Context):
        """Configure starboard system for your server"""
        data = await self.bot.db.fetchrow("SELECT * FROM starboard_config WHERE guild=$1", ctx.guild.id)
        if not data:
            return await ctx.send_help(ctx.command)
        ignored_channels = await self.bot.db.fetchval(
            "SELECT ignore_channel FROM starboard_config WHERE guild = $1",
            ctx.guild.id
        )
        ig_c_list = ""
        if not ignored_channels:
            ig_c_list = "None"
        else:
            for c in ignored_channels:
                channel_id = ctx.guild.get_channel(int(c))
                ig_c_list += f"{channel_id.mention}, "
            ig_c_list = ig_c_list[:-2]

        embed = discord.Embed(title="Starboard Configuration for this Server")
        embed.add_field(name="Channel", value=data['sb_channel'])
        embed.add_field(name="Amount", value=data['amount'])
        embed.add_field(name="Emoji", value=data['emoji'] or "⭐️")
        embed.add_field(name="Self Star", value=data['self_star'])
        embed.add_field(name="Allow NSFW", value=data['nsfw'])
        embed.add_field(name="Ignored Channel", value=ig_c_list)
        await ctx.send(embed=embed)

    @starboard.command(name="enable")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_messages=True))
    async def starboard_enable(self, ctx: commands.Context):
        """Enable starboard"""
        if await self.bot.db.fetchrow("SELECT * FROM starboard_config WHERE guild=$1", ctx.guild.id):
            return await ctx.send("Starboard already enabled!")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        msg = await ctx.send("What will be the starboard channel? **REMEMBER TO MENTION THE CHANNEL CORRECTLY**")
        channel_value = await self.bot.wait_for('message', check=check)

        try:
            channel_id = int(channel_value.content[2:-1])
        except ValueError:
            await ctx.channel.purge(limit=1)
            await msg.edit(
                content=f'Setup crash because you failed to mention the channel correctly. Please do it like this: {ctx.channel.mention}'
            )
            return

        await ctx.channel.purge(limit=1)
        await msg.edit(content="What will be the starboard amount? Type `default` if you want to default setting, which is 3")
        amount_value = await self.bot.wait_for('message', check=check)
        if amount_value.content.lower() == "default":
            amount = 3
        else:
            try:
                amount = int(amount_value.content)
            except ValueError:
                await ctx.channel.purge(limit=1)
                await ctx.send("Setup crash because you input something that's not a number")
                return

        await ctx.channel.purge(limit=1)
        await self.bot.db.execute(
            """
            INSERT INTO
            starboard_config(guild, sb_channel, amount, emoji, self_star, lock, nsfw, ignore_channel)
            VALUES($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            ctx.guild.id,
            channel_id,
            amount,
            None,
            False,
            False,
            False,
            []
        )
        await msg.edit(content="Starboard Setup complete")

    @starboard.command(name="disable")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_messages=True))
    async def starboard_disable(self, ctx: commands.Context):
        """Disable starboard"""
        await self.bot.db.execute(
            "DELETE FROM starboard_config WHERE guild=$1",
            ctx.guild.id
        )
        await self.bot.db.execute(
            "DELETE FROM starboard_message WHERE guild=$1",
            ctx.guild.id
        )
        await ctx.send("Starboard is now disabled in this server")

    @starboard.command(name="channel")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_channels=True))
    async def starboard_channel(self, ctx: commands.Context, *, channel: discord.TextChannel):
        """Change starboard channel."""
        await self.bot.db.execute(
                "UPDATE starboard_config SET channel = $1 WHERE guild = $2",
                channel.id,
                ctx.guild.id
        )

        await ctx.send(f"Starboard channel set to {channel.mention}")

    @starboard.command(name="amount")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_guild=True))
    async def starboard_amount(self, ctx: commands.Context, *, amount: int):
        """Set starboard amount"""
        data = await self.bot.db.fetchrow("SELECT * FROM starboard_config WHERE guild=$1", ctx.guild.id)

        if not data:
            return await ctx.send("You haven't set up the starboard system. Use `starboard channel` to get start")

        await self.bot.db.execute(
            "UPDATE starboard_config SET amount = $1 WHERE guild = $2",
            amount,
            ctx.guild.id
        )
        await ctx.send(f"Starboard amount set too {amount}.")

    @starboard.command(name="emoji")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_guild=True))
    async def starboard_emoji(self, ctx: commands.Context, *, emoji):
        """Set custom emoji for starboard.
        If you want to use the default star emoji, type 'default'

        Note that this does not work with server emojis
        """
        if emoji == "default":
            await self.bot.db.execute(
                "UPDATE starboard_config SET emoji = $1 WHERE guild = $2",
                None,
                ctx.guild.id
            )
            await ctx.send(f"Starboard emoji reset back to default ⭐️.")
            return

        await self.bot.db.execute(
            "UPDATE starboard_config SET emoji = $1 WHERE guild = $2",
            emoji,
            ctx.guild.id
        )
        await ctx.send(f"Starboard emoji set too {emoji}.")

    @starboard.command(name="selfstar")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_guild=True))
    async def starboard_self_star(self, ctx: commands.Context):
        """Toggle selfstar for starboard"""
        view = Confirm(ctx)
        msg = await ctx.send("Do you want message author to self star their own message?", view=view)

        await view.wait()
        if view.value is None:
            await msg.edit(content="You take too long to respond!", view=None)
        elif view.value:
            await self.bot.db.execute(
                "UPDATE starboard_config SET self_star = $1 WHERE guild = $2",
                True,
                ctx.guild.id
            )
            await msg.edit(content=f"Self Star enabled", view=None)
        else:
            await self.bot.db.execute(
                "UPDATE starboard_config SET self_star = $1 WHERE guild = $2",
                False,
                ctx.guild.id
            )
            await msg.edit(content=f"Self Star disabled", view=None)

    @starboard.command(name="nsfw")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_guild=True))
    async def starboard_nsfw(self, ctx: commands.Context):
        """Toggle nsfw for starboard"""
        view = Confirm(ctx)
        msg = await ctx.send("Do you want to allow starboard messages from nsfw channels?", view=view)

        await view.wait()
        if view.value is None:
            await msg.edit(content="You take too long to respond!", view=None)
        elif view.value:
            await self.bot.db.execute(
                "UPDATE starboard_config SET nsfw = $1 WHERE guild = $2",
                True,
                ctx.guild.id
            )
            await msg.edit(content=f"NSFW enabled", view=None)
        else:
            await self.bot.db.execute(
                "UPDATE starboard_config SET nsfw = $1 WHERE guild = $2",
                False,
                ctx.guild.id
            )
            await msg.edit(content=f"NSFW disabled", view=None)

    @starboard.command(name="ignore-channel")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_channels=True))
    async def ignore_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        """Ignored certain channels from the starboard system"""
        if channel.id in await self.bot.db.fetchval(
                "SELECT ignore_channel FROM starboard_config WHERE guild = $1",
                ctx.guild.id
        ):
            return await ctx.send("Channel already ignored from starboard system")
        await self.bot.db.execute(
            "UPDATE starboard_config SET ignore_channel = ARRAY_APPEND(ignore_channel, $1) WHERE guild = $2",
            channel.id,
            ctx.guild.id
        )
        await ctx.send(f"{channel.mention} successfully ignored from the starboard system")

    @starboard.command(name="unignore-channel")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_channels=True))
    async def unignore_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        """Unignore certain channels from the starboard system"""
        await self.bot.db.execute(
            "UPDATE starboard_config SET ignore_channel = ARRAY_REMOVE(ignore_channel, $1) WHERE guild = $2",
            channel.id,
            ctx.guild.id
        )
        await ctx.send(f"{channel.mention} successfully unignored from the starboard system")

