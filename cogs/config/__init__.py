from .configuration import Configuration
from core import Stancil


async def setup(bot: Stancil):
    await bot.add_cog(Configuration(bot))
