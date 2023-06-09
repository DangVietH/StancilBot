import discord
from discord.ext import commands
from core import Stancil
import inspect
from utilities import time_converter


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
            "SELECT ignore_channel FROM level_config WHERE guild = $1",
            ctx.guild.id
        )
        ig_c_list = ""
        if not ignored_channels:
            ig_c_list = None
        else:
            for c in ignored_channels:
                channel_id = ctx.guild.get_channel(int(c))
                ig_c_list += f"{channel_id.mention}, "
            ig_c_list = ig_c_list[:-2]

        if data['lvl_up_channel']:
            lvl_channel = ctx.guild.get_channel(data['lvl_up_channel']).mention
        else:
            lvl_channel = None

        embed = discord.Embed(title="Leveling Configuration for this Server")
        embed.add_field(name="Announcement Channel", value=lvl_channel)
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
        s1 = await self.bot.db.execute(
            "DELETE FROM level_config WHERE guild=$1",
            ctx.guild.id
        )
        s2 = await self.bot.db.execute(
            "DELETE FROM leveling WHERE guild=$1",
            ctx.guild.id
        )
        if s1 and s2 == 'DELETE 0':
            return await ctx.send("Level Not Enabled in this server")
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

    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def role(self, ctx: commands.Context):
        """Configure reaction or button(comming soon) roles"""
        await ctx.send_help(ctx.command)

    @role.group(invoke_without_command=True, case_insensitive=True)
    async def reaction(self, ctx: commands.Context):
        """Commands to config reaction roles"""
        await ctx.send_help(ctx.command)

    @reaction.command(name="create")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_roles=True))
    async def reaction_create(self, ctx: commands.Context):
        """Create a reaction role"""
        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        msg = await ctx.send("Hello there. Which channel would you like the reaction role message to be in?")
        channel_value = await self.bot.wait_for('message', check=check)

        try:
            channel_id = int(channel_value.content[2:-1])
        except ValueError:
            await ctx.channel.purge(limit=1)
            await msg.edit(
                content=f'Setup crash because you failed to mention the channel correctly. Please do it like this: {ctx.channel.mention}'
            )
            return
        channel = self.bot.get_channel(channel_id)
        await ctx.channel.purge(limit=1)

        await msg.edit(content=f"Alright, the message will be sent to {channel.mention}.\nNow let's setup the embed message. What will be the title of the embed?")
        embed_title = await self.bot.wait_for('message', check=check)
        title = embed_title.content
        embed = discord.Embed(title=title).set_footer(text="This is what the embed will look like")
        await ctx.channel.purge(limit=1)

        await msg.edit(content="What will be the embed description", embed=embed)
        embed_desc = await self.bot.wait_for('message', check=check)
        desc = embed_desc.content
        embed.description = desc
        await ctx.channel.purge(limit=1)

        await msg.edit(content="What will be the embed color (Hex color like this `0x2F3136`. If you want no color, type `skip`)", embed=embed)
        color_hex = await self.bot.wait_for('message', check=check)
        if color_hex.content.lower() == "skip":
            hex_val = None
        else:
            hex_val = int(color_hex.content, 16)
        embed.color = hex_val
        await ctx.channel.purge(limit=1)

        await msg.edit(content=inspect.cleandoc("""
                        Nice, your embed message will look like this. Now it's time to add emojis and role
                        Here's an example on how to format the emojis and role text
                        ```:emoji 1: | @mention role here ; :emoji 2: | @mention another role here```
                        You can add how many reaction roles you want
                        """), embed=embed)
        emoji_roles = await self.bot.wait_for('message', check=check)
        cells = emoji_roles.content.split(";")
        emojis = []
        roles = []
        for cell in cells:
            divider = cell.split("|")
            emojis.append(divider[0].strip())
            roles.append(int(divider[1].strip()[3:-1]))

        await ctx.channel.purge(limit=1)
        embed.remove_footer()
        reaction_role_message = await channel.send(embed=embed)

        await self.bot.db.execute(
            """
            INSERT INTO
            role(message, channel, guild, button, embed_title, embed_desc, embed_color, emojis, roles)
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            reaction_role_message.id,
            channel.id,
            ctx.guild.id,
            False,
            title,
            desc,
            hex_val,
            emojis,
            roles
        )

        for emoji in emojis:
            await reaction_role_message.add_reaction(emoji)

        await msg.edit(content=f"Setup complete. Go to {channel.mention} to see the reaction message.", embed=None)

    @reaction.command(name="add")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_messages=True))
    async def reaction_add(self, ctx: commands.Context, message_id: int, emoji, role: discord.Role):
        """Add more emojis to a reaction role message"""
        data = await self.bot.db.fetchrow("SELECT * FROM role WHERE message=$1", message_id)
        if not data:
            return await ctx.send("This message is not a reaction role message!")
        channel = self.bot.get_channel(data['channel'])
        message = await channel.fetch_message(message_id)
        await message.add_reaction(emoji)
        await self.bot.db.execute(
            "UPDATE role SET emojis = ARRAY_APPEND(emojis, $1) WHERE message = $2",
            emoji,
            message_id
        )
        await self.bot.db.execute(
            "UPDATE role SET roles = ARRAY_APPEND(roles, $1) WHERE message = $2",
            role.id,
            message_id
        )
        await ctx.message.add_reaction("✅")

    @reaction.command(name="remove")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_messages=True))
    async def reaction_remove(self, ctx: commands.Context, message_id: int, emoji):
        """Remove emoji from a reaction role message"""
        data = await self.bot.db.fetchrow("SELECT * FROM role WHERE message=$1", message_id)
        if not data:
            return await ctx.send("This message is not a reaction role message!")
        channel = self.bot.get_channel(data['channel'])
        message = await channel.fetch_message(message_id)

        emojis = await self.bot.db.fetchval(
            "SELECT role_level FROM level_config WHERE guild = $1",
            ctx.guild.id
        )
        roles = await self.bot.db.fetchval(
            "SELECT role_id FROM level_config WHERE guild = $1",
            ctx.guild.id
        )
        role_id = 0

        for i in range(len(roles)):
            if emoji == int(emojis[i]):
                role_id = roles[i]

        await message.clear_reaction(emoji)
        await self.bot.db.execute(
            "UPDATE role SET emojis = ARRAY_REMOVE(emojis, $1) WHERE message = $2",
            emoji,
            message_id
        )
        await self.bot.db.execute(
            "UPDATE role SET roles = ARRAY_REMOVE(roles, $1) WHERE message = $2",
            role_id,
            message_id
        )
        await ctx.message.add_reaction("✅")

    @reaction.command(name="edit")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_messages=True))
    async def reaction_edit(self, ctx: commands.Context, message_id: int):
        """Edit a reaction role message embed"""

        data = await self.bot.db.fetchrow("SELECT * FROM role WHERE message=$1", message_id)
        if not data:
            return await ctx.send("This message is not a reaction role message!")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        msg = await ctx.send("Hello there. Would you like to edit the title ,description or color?")
        choice = await self.bot.wait_for('message', check=check)

        embed = discord.Embed()
        if choice.content.lower() == "title":
            await ctx.channel.purge(limit=1)
            await msg.edit(content="Alright. What will be the new title?")
            title = await self.bot.wait_for('message', check=check)
            embed.title = title.content
            embed.description = data['embed_desc']
            embed.color = data['embed_color']
            await self.bot.db.execute(
                """
                UPDATE role
                SET embed_title = $1
                WHERE message = $2
                """,
                title.content,
                message_id
            )
        elif choice.content.lower() == "description":
            await ctx.channel.purge(limit=1)
            await msg.edit(content="Alright. What will be the new description?")
            desc = await self.bot.wait_for('message', check=check)
            embed.description = desc.content
            embed.title = data['embed_title']
            embed.color = data['embed_color']
            await self.bot.db.execute(
                """
                UPDATE role
                SET embed_desc = $1
                WHERE message = $2
                """,
                desc.content,
                message_id
            )
        elif choice.content.lower() == "color":
            await ctx.channel.purge(limit=1)
            await msg.edit(content="Alright. What will be the new embed color? (Hex color like this `0x2F3136`)")
            color = await self.bot.wait_for('message', check=check)
            color_hex = int(color.content, 16)
            embed.title = data['embed_title']
            embed.description = data['embed_desc']
            embed.color = color_hex
            await self.bot.db.execute(
                """
                UPDATE role
                SET embed_color = $1
                WHERE message = $2
                """,
                color_hex,
                message_id
            )
        else:
            await ctx.channel.purge(limit=1)
            return await msg.edit(
                content="Editor crash because invalid option. The only valid ones are `title`, `description` and `color`")
        await ctx.channel.purge(limit=1)

        channel = self.bot.get_channel(data['channel'])
        message = await channel.fetch_message(message_id)
        await message.edit(embed=embed)
        await msg.edit(content="Editing finish")

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
            ig_c_list = None
        else:
            for c in ignored_channels:
                channel_id = ctx.guild.get_channel(int(c))
                ig_c_list += f"{channel_id.mention}, "
            ig_c_list = ig_c_list[:-2]

        embed = discord.Embed(title="Starboard Configuration for this Server")
        embed.add_field(name="Channel", value=ctx.guild.get_channel(data['sb_channel']).mention)
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
        s1 = await self.bot.db.execute(
            "DELETE FROM starboard_config WHERE guild=$1",
            ctx.guild.id
        )
        s2 = await self.bot.db.execute(
            "DELETE FROM starboard_message WHERE guild=$1",
            ctx.guild.id
        )
        if s1 and s2 == 'DELETE 0':
            return await ctx.send("Starboard Not Enabled in this server")
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

    @starboard.command(name="expire")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_guild=True))
    async def expire(self, ctx: commands.Context, expire_date):
        """Set expire date for every starboard message. Time format includes: s, m, h, d"""

        converted_time = time_converter(expire_date)
        if converted_time == -1:
            return await ctx.send("You didn't format the time correctly. Example of a correct one: `4h`")
        if converted_time == -2:
            return await ctx.send("Time must be an integer. Example of a correct one: `4h`")

        await self.bot.db.execute(
            "UPDATE starboard_config SET expire = $1 WHERE guild = $2",
            converted_time,
            ctx.guild.id
        )
        await ctx.send(f"Setup complete. Every starboard message from now on will expire in {expire_date}.\n**THIS DOES NOT MEAN THE MESSAGE IN THE STARBOARD CHANNEL WILL DELETE ITSELF**")

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

    @starboard.command(name="lock")
    @commands.check_any(has_config_role(), commands.has_permissions(manage_guild=True))
    async def starboard_lock(self, ctx: commands.Context):
        """Locking starboard"""
        view = Confirm(ctx)
        msg = await ctx.send("Do you want to lock starboard?", view=view)

        await view.wait()
        if view.value is None:
            await msg.edit(content="You take too long to respond!", view=None)
        elif view.value:
            await self.bot.db.execute(
                "UPDATE starboard_config SET lock = $1 WHERE guild = $2",
                True,
                ctx.guild.id
            )
            await msg.edit(content=f"Starboard locked", view=None)
        else:
            await self.bot.db.execute(
                "UPDATE starboard_config SET lock = $1 WHERE guild = $2",
                False,
                ctx.guild.id
            )
            await msg.edit(content=f"Starboard unlock", view=None)

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

