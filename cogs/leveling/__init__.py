from .leveling import Leveling
from core import Stancil


async def setup(bot: Stancil):
    await bot.add_cog(Leveling(bot))
