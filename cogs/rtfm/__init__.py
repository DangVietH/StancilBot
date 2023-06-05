from .rtfm import RTFM
from core import Stancil


async def setup(bot: Stancil):
    await bot.add_cog(RTFM(bot))
