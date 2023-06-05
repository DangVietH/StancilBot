from .moderation import Moderation
from core import Stancil


async def setup(bot: Stancil):
    await bot.add_cog(Moderation(bot))
