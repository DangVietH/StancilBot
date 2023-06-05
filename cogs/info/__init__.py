from .info import Info
from core import Stancil


async def setup(bot: Stancil):
    await bot.add_cog(Info(bot))
