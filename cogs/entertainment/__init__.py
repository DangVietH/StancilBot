from .fun import Fun
from .image import Image
from core import Stancil


async def setup(bot: Stancil):
    await bot.add_cog(Fun(bot))
    await bot.add_cog(Image(bot))
