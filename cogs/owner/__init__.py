from .owner import Owner
from core import Stancil


async def setup(bot: Stancil):
    await bot.add_cog(Owner(bot))

