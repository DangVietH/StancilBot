import functools

import discord
from discord.ext import commands
from core import Stancil
from utilities import MenuPages, DefaultPageSource, SecondPageSource
import io
from PIL import Image, ImageDraw, ImageFont


def rank_card_maker(member, level, xp, rank, background, avatar):
    image_width = 900
    image_height = 250

    image = Image.open(io.BytesIO(background)).convert("RGBA")

    image = image.resize((image_width, image_height))

    rectangle_image = Image.new('RGBA', (image_width, image_height))
    rectangle_draw = ImageDraw.Draw(rectangle_image)
    rectangle_draw.rectangle((20, 20, image_width - 20, image_height - 20), fill=(0, 0, 0, 127))
    image = Image.alpha_composite(image, rectangle_image)

    draw = ImageDraw.Draw(image)

    font_big = ImageFont.truetype('assets/font.ttf', 36)
    font_small = ImageFont.truetype('assets/font.ttf', 20)

    needed_xp = 100 * 2 * ((1 / 2) * level)
    draw.text((248, 48), f"{member}", fill=(225, 0, 92), font=font_big)
    draw.text((641, 48), f"Rank #{rank}", fill=(225, 0, 92), font=font_big)
    draw.text((248, 130), f"Level {level}", fill=(225, 0, 92), font=font_small)
    draw.text((641, 130), f"{xp} / {needed_xp} XP", fill=(225, 0, 92), font=font_small)

    draw.rounded_rectangle((242, 182, 803, 208), fill=(70, 70, 70), outline=(225, 0, 92), radius=13, width=3)

    bar_length = 245 + xp / needed_xp * 205
    draw.rounded_rectangle((245, 185, bar_length, 205), fill=(225, 0, 92), radius=10)

    # read JPG from buffer to Image
    AVATAR_SIZE = 200
    avatar_image = Image.open(avatar)
    avatar_image = avatar_image.resize((AVATAR_SIZE, AVATAR_SIZE))

    circle_image = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE))
    circle_draw = ImageDraw.Draw(circle_image)
    circle_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)

    x = 40
    y = (image_height - AVATAR_SIZE) // 2
    image.paste(avatar_image, (x, y), circle_image)

    buffer = io.BytesIO()

    # save PNG in buffer
    image.save(buffer, format='PNG')

    # move to beginning of buffer so `send()` it will read from beginning
    buffer.seek(0)

    # return data
    return buffer


class Leveling(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot

    @commands.command()
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        """Show someone's xp"""
        await ctx.channel.typing()
        member = member or ctx.author

        data = await self.bot.db.fetchrow(
            "SELECT * FROM leveling WHERE guild=$1 AND member=$2",
            ctx.guild.id,
            member.id
        )

        if not data:
            return await ctx.send("This member hasn't send a message in this server")

        rank = 0
        lvl = 0
        xp = data['xp']
        for record in await self.bot.db.fetch(
            "SELECT * FROM leveling WHERE guild=$1 ORDER BY xp DESC", ctx.guild.id
        ):
            rank += 1
            if record["member"] == member.id:
                break

        while True:
            if xp < ((100 / 2 * (lvl ** 2)) + (100 / 2 * lvl)):
                break
            lvl += 1

        xp -= ((100 / 2 * ((lvl - 1) ** 2)) + (100 / 2 * (lvl - 1)))

        if data['card_bg'] is None:
            img_link = "https://cdn.discordapp.com/attachments/875886792035946496/953533593207062588/2159517.jpeg"
        else:
            img_link = data['card_bg']

        resp = await self.bot.session.get(img_link)
        background = await resp.read()

        avatar_asset = member.display_avatar.replace(format='jpg', size=128)
        buffer_avatar = io.BytesIO(await avatar_asset.read())

        buffer_avatar = io.BytesIO()
        await avatar_asset.save(buffer_avatar)
        buffer_avatar.seek(0)

        # run in async executor
        sync_func = functools.partial(rank_card_maker, member, lvl, xp, rank, background, buffer_avatar)
        results = await self.bot.loop.run_in_executor(None, sync_func)
        await ctx.send(file=discord.File(results, 'rank.png'))

    @commands.command(aliases=['top'])
    async def leaderboard(self, ctx: commands.Context):
        """Display server level leaderboard"""
        data = await self.bot.db.fetch(
            "SELECT * FROM leveling WHERE guild=$1 ORDER BY xp DESC", ctx.guild.id
        )

        menu_data = []
        rank = 0
        for member in data:
            rank += 1
            menu_data.append(
                (
                    f"{rank}: {ctx.guild.get_member(member['member'])}",
                    f"**Level:** {member['level']} **XP:** {member['xp']}"
                )
            )
        page = MenuPages(DefaultPageSource(f"Leaderboard of {ctx.guild.name}", menu_data), ctx)
        await page.start()

    @commands.command(name="role-reward-list")
    async def role_reward_list(self, ctx: commands.Context):
        """Show the list of roles rewards"""
        role_level = await self.bot.db.fetchval(
            "SELECT role_level FROM level_config WHERE guild = $1",
            ctx.guild.id
        )
        role_id = await self.bot.db.fetchval(
            "SELECT role_id FROM level_config WHERE guild = $1",
            ctx.guild.id
        )
        menu_data = []
        for i in range(len(role_level)):
            menu_data.append((f"**{role_level[i]}**", ctx.guild.get_role(int(role_id[i])).mention))

        page = MenuPages(SecondPageSource(f"{ctx.guild.name} Role Rewards", menu_data), ctx)
        await page.start()

    @commands.command(name="set-background")
    async def set_background(self, ctx: commands.Context, *, link):
        """Set custom background for your rankcard."""
        await self.bot.db.execute(
            "UPDATE leveling SET card_bg = $1 WHERE guild = $2 AND member = $3",
            link,
            ctx.guild.id,
            ctx.author.id
        )
        await ctx.send("Custom rankcard background set.")
