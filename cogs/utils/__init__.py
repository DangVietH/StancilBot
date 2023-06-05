from .utils import Utils
from .tag import Tag
from core import Stancil


async def setup(bot: Stancil):
    await bot.add_cog(Tag(bot))
    await bot.add_cog(Utils(bot))
