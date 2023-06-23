import random
import discord
from discord.ext import commands
from core import Stancil
import asyncio
import re


class TriviaButton(discord.ui.Button['TriviaView']):
    def __init__(self, label, value: bool, click_color):
        super().__init__(style=discord.ButtonStyle.grey, label=label)
        self.click_color = click_color
        self.value = value

    async def callback(self, interaction: discord.Interaction):

        self.style = self.click_color

        assert self.view is not None
        view: TriviaView = self.view

        if self.value:
            view.embed.description = f"Correct! The answer is **{view.answer}**"
        else:
            view.embed.description = f"Wrong! The correct answer is **{view.answer}**"

        for child in view.children:
            child.disabled = True

        await interaction.response.edit_message(embed=view.embed, view=view)
        view.stop()


class TriviaView(discord.ui.View):
    def __init__(self, ctx: commands.Context, question, category, difficulty, option: list, answer):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.question = question
        self.category = category
        self.difficulty = difficulty
        self.option = option
        self.answer = answer
        self.embed = discord.Embed()
        self.message = None

    async def start(self) -> None:
        # create embed
        self.embed.title = self.question
        self.embed.add_field(name="Category", value=self.category)
        self.embed.add_field(name="Difficulty", value=self.difficulty)

        # adding buttons
        for o in self.option:
            if o == self.answer:
                value = True
                click_color = discord.ButtonStyle.green
            else:
                value = False
                click_color = discord.ButtonStyle.red
            self.add_item(TriviaButton(o, value, click_color))

        self.message = await self.ctx.send(embed=self.embed, view=self)

    async def on_timeout(self) -> None:
        self.embed.description = f"Timeout. The correct answer is {self.answer}"
        for child in self.children:
            child.disabled = True
        await self.message.edit(embed=self.embed, view=self)

    async def interaction_check(self, interaction) -> bool:
        if interaction.user == self.ctx.author:
            return True
        else:
            await interaction.response.send_message("You can't use these buttons", ephemeral=True)
            return False


class Fun(commands.Cog):
    """Fun Commands"""

    def __init__(self, bot: Stancil):
        self.bot = bot

    @property
    def emoji(self):
        return "😄"

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trivia(self, ctx: commands.Context):
        """Play some trivia"""
        resp = await self.bot.session.get(f"https://opentdb.com/api.php?amount=1")
        resp_json = await resp.json()

        data = resp_json['results'][0]
        options = [re.sub("&.*?;", "", k) for k in data["incorrect_answers"]]
        correct_answer = re.sub("&.*?;", "", data["correct_answer"])
        options.append(correct_answer)
        random.shuffle(options)

        view = TriviaView(
            ctx,
            re.sub("&.*?;", "", data["question"]),
            data["category"],
            data["difficulty"],
            options,
            correct_answer
        )
        await view.start()

    @commands.command(aliases=["iqrate"])
    async def iq(self, ctx: commands.Context):
        """Rate your iq"""
        iq = random.randint(0, 1000)
        await ctx.send(f"Your IQ score is {iq}")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def quote(self, ctx: commands.Context):
        """Get a random quote"""
        resp = await self.bot.session.get(f"https://zenquotes.io/api/random")
        data = await resp.json()
        await ctx.send(f"{data[0]['q']}\n {data[0]['a']}")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def dogfact(self, ctx: commands.Context):
        """Get a dog fact"""
        resp = await self.bot.session.get(f"https://some-random-api.com/facts/dog")
        data = await resp.json()
        await ctx.send(f"**Dog Fact:** {data['fact']}")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def catfact(self, ctx: commands.Context):
        """Get a cat fact"""
        resp = await self.bot.session.get(f"https://some-random-api.com/facts/cat")
        data = await resp.json()
        await ctx.send(f"**Cat Fact:** {data['fact']}")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def birdfact(self, ctx: commands.Context):
        """Get a bird fact"""
        resp = await self.bot.session.get(f"https://some-random-api.com/facts/bird")
        data = await resp.json()
        await ctx.send(f"**Bird Fact:** {data['fact']}")

    @commands.command(aliases=["cock", 'dong'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def pp(self, ctx: commands.Context, *, member: discord.Member = None):
        """Measure your pp"""
        member = member or ctx.author
        await ctx.send(
            embed=discord.Embed(
                title=f"{member} pp size",
                description=f"8{'=' * random.randint(0, 50)}D",
                color=discord.Color.purple()
            )
        )

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def emojify(self, ctx: commands.Context, *, text):
        """Emojify your text. Note that special characters like ă will not work"""
        emojis = []
        for s in text:
            if s.isdecimal():
                num2emo = {'0': 'zero', '1': 'one', '2': 'two',
                           '3': 'three', '4': 'four', '5': 'five',
                           '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
                emojis.append(f":{num2emo.get(s)}:")
            elif s.isalpha():
                emojis.append(f":regional_indicator_{s.lower()}:")
            else:
                emojis.append(s)
        await ctx.send(''.join(emojis))

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def joke(self, ctx: commands.Context):
        """Get a joke"""
        resp = await self.bot.session.get(f"https://some-random-api.com/joke")
        data = await resp.json()
        await ctx.send(data['joke'])

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def pokedex(self, ctx: commands.Context, *, pokemon):
        """Get info about a Pokémon"""
        resp = await self.bot.session.get(
            f"https://some-random-api.com/pokemon/pokedex", params={"pokemon": pokemon}
        )
        data = await resp.json()

        if data.get('error'):
            return await ctx.send(f"Received unexpected error: {data['error']}")
        embed = discord.Embed(title=f"{data['name']} - {data['id']}", description=data['description'])
        embed.add_field(name="Type", value=", ".join(poketype for poketype in data['type']))
        embed.add_field(name="Species", value=", ".join(species for species in data['species']))
        embed.add_field(name="Generation", value=data['generation'])
        embed.add_field(name="Abilities", value=", ".join(abilities for abilities in data['abilities']))
        embed.add_field(name="Height", value=data['height'])
        embed.add_field(name="Weight", value=data['weight'])
        embed.add_field(name="Gender", value=", ".join(gender for gender in data['gender']))
        embed.add_field(name="Base Experience", value=data['base_experience'])
        embed.add_field(name="Egg group", value=", ".join(egg_groups for egg_groups in data['egg_groups']))
        embed.add_field(name="HP", value=data['stats']['hp'])
        embed.add_field(name="Attack", value=data['stats']['attack'])
        embed.add_field(name="Defense", value=data['stats']['defense'])
        embed.add_field(name="Speed Attack", value=data['stats']['sp_def'])
        embed.add_field(name="Speed Defense", value=data['stats']['sp_def'])
        embed.add_field(name="Speed", value=data['stats']['speed'])
        embed.add_field(name="Total", value=data['stats']['total'])
        embed.add_field(name="Evolution Stage", value=data['family']['evolutionStage'])
        if data['family']['evolutionLine']:
            embed.add_field(name="Evolution Line", value=", ".join(eline for eline in data['family']['evolutionLine']))
        embed.set_thumbnail(url=data['sprites']['animated'])
        await ctx.send(embed=embed)

    @commands.command(name="8ball")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _8ball(self, ctx: commands.Context, *, question):
        """Answering your questions"""
        answer = [
            'It is Certain.',
            'It is decidedly so',
            'Without a doubt.',
            'Yes definitely.',
            'You may rely on it',
            'As I see it, yes.',
            'Most likely.',
            'Outlook good',
            'Yes',
            'Signs point to yes.',
            'Reply hazy, try again.',
            'Ask again later.',
            'Better not tell you now.',
            'Cannot predict now.',
            'Concentrate and ask again.',
            "Don't count on it.",
            'My reply is no.',
            'My sources say no.',
            'Outlook not so good',
            'Very doubtful'
        ]
        await ctx.send(f"**Q:** {question}\n**A:** {random.choice(answer)}")

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def hack(self, ctx: commands.Context, member: discord.Member = None):
        """Pretend to hack someone"""
        if member is None:
            return await ctx.send("I don't see someone to hack, maybe later?")
        msg = await ctx.send("`$python hack.py`")
        await asyncio.sleep(2)
        await msg.edit(content="Get user.id")
        await asyncio.sleep(2)
        await msg.edit(content="Start sql injection")
        await asyncio.sleep(2)
        await msg.edit(content=f"```sql\nSELECT * FROM users WHERE user_id = {member.id}--'  AND password = ''```")
        await asyncio.sleep(2)
        await msg.edit(content=f"email: `{member.name}@gmail.com`\npassword: `********` \nip address: `1.2.7.500`")
        await asyncio.sleep(2)
        await msg.edit(content="Checking user activity")
        await asyncio.sleep(2)
        await msg.edit(content="Report to discord for violating TOS")
        await asyncio.sleep(2)
        await msg.edit(content=f"Finish hacking {member.name}")
