import discord
from discord.ext import commands
from core import Stancil


# starboard embed generator
def sb_embed_generator(message: discord.Message):
    embed = discord.Embed(color=discord.Color.yellow(), timestamp=message.created_at)
    embed.set_author(name=f"{message.author.display_name}", icon_url=message.author.display_avatar.url)
    embed.add_field(name="Source", value=f"[Jump]({message.jump_url})")
    embed.set_footer(text=f"ID: {message.id}")

    if message.content:
        embed.description = message.content

    attach = message.attachments[0] if message.attachments else None
    if attach:
        if attach.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
            embed.set_image(url=attach.url)
        else:
            embed.add_field(name='Attachment', value=f'[**{attach.filename}**]({attach.url})', inline=False)
    if message.embeds:
        image = message.embeds[0].image.url
        if image:
            embed.set_image(url=image)
    return embed


class Starboard(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not self.bot.get_guild(payload.guild_id):
            return

        if payload.member.bot:
            return

        sb_config_data = await self.bot.db.fetchrow(
            "SELECT * FROM starboard_config WHERE guild=$1",
            payload.guild_id
        )
        if not sb_config_data:
            return

        if payload.channel_id in await self.bot.db.fetchval(
                "SELECT ignore_channel FROM starboard_config WHERE guild = $1",
                payload.guild_id
        ):
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        sb_channel = self.bot.get_channel(sb_config_data['sb_channel'])
        emoji = "⭐" if sb_config_data['emoji'] is None else sb_config_data['emoji']

        if str(payload.emoji) != emoji:
            return

        if sb_config_data['lock'] is True:
            return
        if channel.id == sb_channel.id:
            return
        if channel.is_nsfw() and sb_config_data['nsfw'] is False:
            return

        reacts = list(filter(lambda r: str(r.emoji) == emoji, message.reactions))
        if reacts:
            react = [user async for user in message.reactions[0].users()]

            # in case that guild disable self star
            if message.author.id in react and sb_config_data['self_star'] is False:
                react.pop(react.index(message.author.id))

            if len(react) >= sb_config_data['amount']:
                message_stats = await self.bot.db.fetchrow(
                    "SELECT * FROM starboard_message WHERE message=$1",
                    payload.message_id
                )

                if not message_stats:
                    new_star_message = await sb_channel.send(
                        f"{emoji} **{len(react)} |** {channel.mention}",
                        embed=sb_embed_generator(message)
                    )
                    await self.bot.db.execute(
                        """
                        INSERT INTO starboard_message(message, channel, sb_message, guild, amount)
                        VALUES($1, $2, $3, $4, $5)
                        """,
                        payload.message_id,
                        payload.channel_id,
                        new_star_message.id,
                        payload.guild_id,
                        len(react)
                    )
                else:
                    sb_message = await sb_channel.fetch_message(message_stats['sb_message'])
                    await sb_message.edit(
                        content=f"{emoji} **{len(react)} |** {channel.mention}",
                        embed=sb_embed_generator(message)
                    )
                    await self.bot.db.execute(
                        """
                        UPDATE starboard_message
                        SET amount = $1
                        WHERE message = $2
                        """,
                        len(react),
                        payload.message_id
                    )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if not self.bot.get_guild(payload.guild_id):
            return

        sb_config_data = await self.bot.db.fetchrow(
            "SELECT * FROM starboard_config WHERE guild=$1",
            payload.guild_id
        )
        if not sb_config_data:
            return

        if payload.channel_id in await self.bot.db.fetchval(
                "SELECT ignore_channel FROM starboard_config WHERE guild = $1",
                payload.guild_id
        ):
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        sb_channel = self.bot.get_channel(sb_config_data['sb_channel'])
        emoji = "⭐" if sb_config_data['emoji'] is None else sb_config_data['emoji']

        if str(payload.emoji) != emoji:
            return

        if sb_config_data['lock'] is True:
            return
        if channel.id == sb_channel.id:
            return
        if channel.is_nsfw() and sb_config_data['nsfw'] is False:
            return

        reacts = list(filter(lambda r: str(r.emoji) == emoji, message.reactions))
        if reacts:
            react = [user async for user in message.reactions[0].users()]

            # in case that guild disable self star
            if message.author.id in react and sb_config_data['self_star'] is False:
                react.pop(react.index(message.author.id))

            message_stats = await self.bot.db.fetchrow(
                "SELECT * FROM starboard_message WHERE message=$1",
                payload.message_id
            )

            if not message_stats:
                return

            sb_message = await sb_channel.fetch_message(message_stats['sb_message'])

            if not react or len(react) >= sb_config_data['amount']:
                await sb_message.edit(
                    content=f"{emoji} **{len(react)} |** {channel.mention}",
                    embed=sb_embed_generator(message)
                )
                await self.bot.db.execute(
                    """
                    UPDATE starboard_message
                    SET amount = $1
                    WHERE message = $2
                    """,
                    len(react),
                    payload.message_id
                )
            else:
                await sb_message.delete()
                await self.bot.db.execute(
                    "DELETE FROM starboard_message WHERE message=$1",
                    payload.message_id
                )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        message_data = await self.bot.db.fetchrow(
            "SELECT * FROM starboard_message WHERE message=$1",
            after.id
        )
        if not message_data:
            return

        guild_data = await self.bot.db.fetchrow(
            "SELECT * FROM starboard_config WHERE guild=$1",
            after.guild.id
        )
        sb_channel = self.bot.get_channel(guild_data['sb_channel'])
        sb_message = await sb_channel.fetch_message(message_data['sb_message'])

        await sb_message.edit(
            content=f"{guild_data['emoji']} **{message_data['amount']} |** {self.bot.get_channel(message_data['channel']).mention}",
            embed=sb_embed_generator(after)
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageUpdateEvent):
        stats = await self.bot.db.execute(
            "DELETE FROM starboard_message WHERE message=$1 and guild=$2",
            payload.message_id,
            payload.guild_id
        )
        if stats == 'DELETE 0':
            return


async def setup(bot: Stancil):
    await bot.add_cog(Starboard(bot))

